#!/usr/bin/env python3
"""Download a complete HF repository, folders or exact files. See accompanying README."""
from __future__ import annotations

import argparse
import fnmatch
import getpass
import json
import os
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED


class SelectionError(ValueError):
    pass


def remote_path(value: str) -> str:
    value = value.replace('\\', '/')
    if value in ('.', './', '/'):
        return ''
    if value.startswith('/') or ':' in value:
        raise argparse.ArgumentTypeError('Use a relative path inside the repository, not a URL/local path.')
    value = value.rstrip('/')
    if not value or any(p in ('', '.', '..') for p in value.split('/')):
        raise argparse.ArgumentTypeError('Invalid repository path.')
    return value


def parser_for_cli():
    p = argparse.ArgumentParser(description='Tai repo, folder de quy hoac file tu Hugging Face.')
    p.add_argument('--repo', required=True, help='Repository ID: OWNER/NAME (not URL)')
    p.add_argument('--repo-type', choices=['dataset', 'model', 'space'], default='dataset')
    p.add_argument('--revision', default='main', help='Branch, tag or commit')
    p.add_argument('--all', action='store_true', help='Download entire repository')
    p.add_argument('--folder', action='append', type=remote_path, default=[], help='Folder; repeatable')
    p.add_argument('--file', action='append', type=remote_path, default=[], help='Exact file; repeatable')
    p.add_argument('--path', action='append', type=remote_path, default=[], help='Auto-detect file/folder; repeatable')
    p.add_argument('--include', action='append', default=[], help='Glob on full repo-relative file path; repeatable')
    p.add_argument('--exclude', action='append', default=[], help='Exclude glob; repeatable; wins over include')
    p.add_argument('--output', default='./downloaded_data', help='Local parent folder')
    p.add_argument('--workers', type=int, default=4, help='Parallel file downloads, >= 1')
    p.add_argument('--retries', type=int, default=5, help='Extra retries for network/temporary file errors, >= 0')
    p.add_argument('--rate-limit-retries', type=int, default=0,
                   help='Maximum retries for HTTP 429; 0 = retry indefinitely (default)')
    p.add_argument('--rate-limit-max-wait', type=int, default=180,
                   help='Maximum seconds of waiting per 429, >= 1 (default: 180)')
    p.add_argument('--error-log', default=None,
                   help='JSONL path for failed files (default: OUTPUT_failed.jsonl beside OUTPUT)')
    p.add_argument('--dry-run', action='store_true', help='List selected files and bytes without downloading')
    p.add_argument('--force-download', action='store_true', help='Download again even when cached')
    auth = p.add_mutually_exclusive_group()
    auth.add_argument('--force-login', action='store_true', help='Prompt for a new personal access token')
    auth.add_argument('--anonymous', action='store_true', help='No token, public repositories only')
    return p


def status_code(exc): # type: ignore
    return getattr(getattr(exc, 'response', None), 'status_code', None)


def error_label(exc):
    # Do not print raw exceptions: signed URLs or credentials may appear in them.
    status = status_code(exc)
    winerror = getattr(exc, 'winerror', None)
    return type(exc).__name__ + (f' (HTTP {status})' if status else
                                   f' (WinError {winerror})' if winerror else '')


def transient(exc):
    import httpx
    status = status_code(exc)
    return (
        isinstance(exc, (httpx.TransportError, TimeoutError, ConnectionError, FileExistsError))
        or getattr(exc, 'winerror', None) == 183
        or status in (408, 425, 429)
        or (status is not None and 500 <= status <= 599)
    )


def retry_after_seconds(exc):
    response = getattr(exc, 'response', None)
    headers = getattr(response, 'headers', None)
    value = headers.get('Retry-After') if headers is not None else None
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        try:
            when = parsedate_to_datetime(value)
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None


class RateLimitGate:
    """Shared waiting gate: a 429 pauses new requests from every worker."""

    def __init__(self):
        self._lock = threading.Lock()
        self._until = 0.0

    def pause(self, seconds):
        with self._lock:
            self._until = max(self._until, time.monotonic() + seconds)

    def wait(self, stop):
        while True:
            if stop.is_set():
                raise InterruptedError('Stopped')
            with self._lock:
                remaining = self._until - time.monotonic()
            if remaining <= 0:
                return
            if stop.wait(remaining):
                raise InterruptedError('Stopped')


def retry_call(func, retries, stop, gate, max_429=0, max_wait=180, context=''):
    other_errors = rate_errors = 0
    while True:
        gate.wait(stop)
        try:
            return func()
        except Exception as exc:
            if stop.is_set():
                raise InterruptedError('Stopped') from exc

            if status_code(exc) == 429:
                rate_errors += 1
                if max_429 and rate_errors > max_429:
                    raise
                # Retry-After (seconds/date) takes precedence over backoff.
                suggested = retry_after_seconds(exc) or 0
                seconds = min(max_wait, max(suggested, 5 * 2 ** min(rate_errors - 1, 6)))
                gate.pause(seconds)
                if rate_errors == 1 or rate_errors % 5 == 0:
                    print(f'HTTP 429 (rate limit){": " + context if context else ""}: '
                          f'cho {seconds:.0f}s, thu lai lan {rate_errors}...', flush=True)
                continue

            if not transient(exc) or other_errors >= retries:
                raise
            other_errors += 1
            seconds = min(2 ** (other_errors - 1), 30)
            if stop.wait(seconds):
                raise InterruptedError('Stopped') from exc


def authenticate(api, args, stop, retry):
    from huggingface_hub import get_token, login
    if args.anonymous:
        print('Che do cong khai: khong gui token.')
        return False
    token = None if args.force_login else get_token()
    if token:
        try:
            user = retry(lambda: api.whoami(token=token), context='whoami')
            print('Da dang nhap:', user.get('name', '(unknown)'))
            return token
        except Exception as exc:
            status = getattr(getattr(exc, 'response', None), 'status_code', None)
            if status not in (401, 403):
                raise  # Network failures do not prove the token is invalid.
            print('Token bi tu choi. Can dang nhap lai.')
    if not sys.stdin.isatty():
        raise SelectionError('Khong co token hop le. Cap HF_TOKEN qua secrets/environment, hoac chay trong terminal tuong tac.')
    print('Tao personal token co quyen Read: https://huggingface.co/settings/tokens')
    print('Token nhap an; khong gui token vao chat. Enter de huy.')
    token = getpass.getpass('HF token: ').strip()
    if not token:
        raise SelectionError('Da huy dang nhap.')
    user = retry(lambda: api.whoami(token=token), context='whoami')
    # Persist this token via the official API. Never store it in source or output.
    retry(lambda: login(token=token, add_to_git_credential=False), context='login')
    print('Dang nhap thanh cong:', user.get('name', '(unknown)'))
    # Pass the entered token explicitly; an old HF_TOKEN cannot override this run.
    return token


def collect_files(api, args, token, commit, stop, retry):
    from huggingface_hub.hf_api import RepoFile, RepoFolder
    common = dict(repo_id=args.repo, repo_type=args.repo_type, revision=commit, token=token)
    found = {}
    requests = [('folder', x) for x in args.folder] + [('file', x) for x in args.file] + [('auto', x) for x in args.path]
    if args.all:
        requests = [('folder', '')]

    def add(entry):
        if not isinstance(entry, RepoFile):
            return
        name = entry.path
        if args.include and not any(fnmatch.fnmatchcase(name, pat) for pat in args.include):
            return
        if any(fnmatch.fnmatchcase(name, pat) for pat in args.exclude):
            return
        is_new = name not in found
        found[name] = entry.size
        if is_new and len(found) % 10000 == 0:
            print(f'Dang lap danh sach: {len(found)} file...', flush=True)

    scanned = set()
    for kind, path in requests:
        if path:
            entries = retry(lambda: api.get_paths_info(paths=[path], **common), context='check ' + path)
            item = next((x for x in entries if x.path == path), None)
            if item is None:
                raise SelectionError(f'Khong tim thay: {path}')
            is_file = isinstance(item, RepoFile)
            if kind == 'file' and not is_file:
                raise SelectionError(f'--file phai la file: {path}')
            if kind == 'folder' and not isinstance(item, RepoFolder):
                raise SelectionError(f'--folder phai la folder: {path}')
            if is_file:
                add(item)
                continue
        elif kind == 'file':
            raise SelectionError('--file khong the la goc repo.')
        if any(path == root or not root or path.startswith(root + '/') for root in scanned):
            continue

        def scan():
            for entry in api.list_repo_tree(path_in_repo=path or None, recursive=True, **common):
                if stop.is_set():
                    raise InterruptedError('Stopped')
                add(entry)
        retry(scan, context='list ' + (path or '/'))
        scanned.add(path)
    return found


def local_target(output, name):
    # Validate remote paths before any writes; guard both POSIX and Windows.
    if remote_path(name) != name or not name:
        raise SelectionError(f'Duong dan Hub khong hop le: {name}')
    target = output.joinpath(*name.split('/'))
    try:
        target.resolve().relative_to(output.resolve())
    except ValueError:
        raise SelectionError(f'Duong dan vuot thu muc dich: {name}') from None
    if os.name == 'nt':
        reserved = {'CON', 'PRN', 'AUX', 'NUL'} | {f'{x}{i}' for x in ('COM', 'LPT') for i in range(1, 10)}
        for part in name.split('/'):
            if any(c in part for c in '<>"|?*') or part.endswith((' ', '.')) or part.split('.')[0].upper() in reserved:
                raise SelectionError(f'Ten file khong tuong thich Windows: {name}')
    if name == '.cache/huggingface' or name.startswith('.cache/huggingface/'):
        raise SelectionError('Repo path conflicts with local Hugging Face download metadata: ' + name)
    return target


def download_files(files, args, token, commit, output, stop, retry, rejected=None):
    from huggingface_hub import hf_hub_download
    from tqdm.auto import tqdm

    rejected = rejected or {}
    error_log = (Path(args.error_log).expanduser().resolve() if args.error_log
                 else output.parent / (output.name + '_failed.jsonl'))
    error_fp = None
    try:
        error_log.parent.mkdir(parents=True, exist_ok=True)
        error_fp = error_log.open('w', encoding='utf-8')
    except OSError as exc:
        print('CANH BAO: Khong mo duoc error log: ' + error_label(exc), flush=True)

    def log_failure(name, exc):
        nonlocal error_fp
        label = exc if isinstance(exc, str) else error_label(exc)
        if error_fp is not None:
            try:
                error_fp.write(json.dumps({'path': name, 'error': label}, ensure_ascii=False) + '\n')
                error_fp.flush()
            except OSError:
                print('CANH BAO: Khong ghi duoc error log.', flush=True)
                error_fp.close()
                error_fp = None

    succeeded = skipped = 0
    failed = len(rejected)
    for name, reason in rejected.items():
        print(f'SKIP: {name}: {reason}', flush=True)
        log_failure(name, reason)

    iterator = iter(files.items())

    def download(item):
        name, expected_size = item
        target = local_target(output, name)

        def valid_file():
            return target.is_file() and (
                expected_size is None or target.stat().st_size == expected_size
            )

        # Resume: an existing file matching the expected size needs no re-download.
        if not args.force_download and valid_file():
            return 'skipped'

        def fetch(force):
            try:
                return hf_hub_download(
                    repo_id=args.repo, repo_type=args.repo_type, revision=commit,
                    filename=name, local_dir=str(output), token=token,
                    force_download=force
                )
            except FileExistsError:
                # Another process might have finished this file while we were downloading.
                if valid_file():
                    return str(target)
                raise

        retry(lambda: fetch(args.force_download), context=name)
        if not valid_file():
            # Incorrect/truncated download: try a fresh copy.
            retry(lambda: fetch(True), context=name)
        if not valid_file():
            raise OSError('Downloaded size mismatch')
        return 'downloaded'

    pool = ThreadPoolExecutor(max_workers=args.workers)
    pending = {}
    try:
        def enqueue():
            item = next(iterator, None)
            if item is not None:
                pending[pool.submit(download, item)] = item[0]

        for _ in range(min(args.workers, len(files))):
            enqueue()
        with tqdm(total=len(files) + len(rejected), initial=len(rejected),
                  desc='Files', unit='file') as progress:
            while pending:
                done, _ = wait(pending, timeout=0.5, return_when=FIRST_COMPLETED)
                for future in done:
                    name = pending.pop(future)
                    try:
                        result = future.result()
                        succeeded += 1
                        if result == 'skipped':
                            skipped += 1
                    except Exception as exc:
                        failed += 1
                        tqdm.write(f'FAILED (bo qua): {name}: {error_label(exc)}')
                        log_failure(name, exc)
                    progress.update(1)
                    enqueue()
    except KeyboardInterrupt:
        stop.set()
        for future in pending:
            future.cancel()
        print('\\nDang dung; cho ket noi dang chay ket thuc...', flush=True)
        raise
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
        if error_fp is not None:
            error_fp.close()

    print(f'KET QUA: {succeeded} thanh cong (trong do {skipped} da ton tai), '
          f'{failed} loi, tong {len(files) + len(rejected)} file.')
    print(f'Danh sach file loi: {error_log if error_log.exists() else "(khong ghi duoc)"}')
    print('Chay lai cung lenh/output de thu lai cac file loi; file du kich thuoc se duoc bo qua.')
    return 1 if failed else 0


def main(argv=None):
    p = parser_for_cli()
    args = p.parse_args(argv)
    if (args.workers < 1 or args.retries < 0 or
            args.rate_limit_retries < 0 or args.rate_limit_max_wait < 1):
        p.error('--workers >= 1; --retries >= 0; --rate-limit-retries >= 0; --rate-limit-max-wait >= 1')
    if '://' in args.repo or args.repo.startswith('/') or len(args.repo.split('/')) > 2:
        p.error('--repo la ID, khong phai URL; vi du OWNER/NAME')
    selectors = args.folder or args.file or args.path
    if args.all and selectors:
        p.error('--all khong di kem --folder/--file/--path')
    if not args.all and not selectors:
        p.error('Chon --all, --folder, --file hoac --path; xem --help')
    stop = threading.Event()
    gate = RateLimitGate()

    def retry(func, context=''):
        return retry_call(func, args.retries, stop, gate,
                          args.rate_limit_retries, args.rate_limit_max_wait, context)

    try:
        from huggingface_hub import HfApi
        api = HfApi()
        token = authenticate(api, args, stop, retry)
        info = retry(lambda: api.repo_info(
            repo_id=args.repo, repo_type=args.repo_type,
            revision=args.revision, token=token
        ), context='repo_info')
        commit = info.sha
        if not commit:
            raise SelectionError('Khong lay duoc commit; dung de tranh tai lan lon phien ban.')
        print(f'Repo: {args.repo} [{args.repo_type}] | commit: {commit}', flush=True)
        print('Dang liet ke file...', flush=True)
        files = collect_files(api, args, token, commit, stop, retry)
        if not files:
            raise SelectionError('Khong co file phu hop. Kiem tra path/include/exclude/revision.')
        output = Path(args.output).expanduser().resolve()
        seen = set()
        valid_files, rejected = {}, {}
        for name, size in files.items():
            try:
                target = local_target(output, name)
                key = os.path.normcase(str(target))
                if key in seen:
                    raise SelectionError('Trung duong dan sau khi chuyen sang he thong file')
                seen.add(key)
                valid_files[name] = size
            except (SelectionError, OSError, ValueError) as exc:
                rejected[name] = str(exc) if isinstance(exc, SelectionError) else error_label(exc)
        total = sum(size for size in files.values() if isinstance(size, int))
        print(f'Da chon: {len(files)} file, {total:,} bytes ({total / 1024**3:.3f} GiB).')
        print(f'Dich: {output}')
        print('Dung luong tren la tong file duoc chon, khong phai so byte con phai tai.')
        if args.dry_run:
            for name, size in files.items():
                print(f'{size}\t{name}')
            return 0
        output.mkdir(parents=True, exist_ok=True)
        return download_files(valid_files, args, token, commit, output, stop, retry, rejected)
    except ImportError as exc:
        print('Thieu dependency. Chay: python -m pip install -U "huggingface_hub>=1.0,<2"', file=sys.stderr)
        print(error_label(exc), file=sys.stderr)
        return 1
    except SelectionError as exc:
        print(f'LOI: {exc}', file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        stop.set()
        print('\nDa huy. Chay lai cung lenh/output/commit de tiep tuc.', file=sys.stderr)
        return 130
    except Exception as exc:
        print('LOI: ' + error_label(exc), file=sys.stderr)
        print('Kiem tra repo/type/revision, quyen token, ket noi mang va dung luong/quyen ghi.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())