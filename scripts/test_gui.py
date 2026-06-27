"""完整端到端测试 - 模拟 GUI 实际执行流程"""
import sys, os, subprocess, time, threading, shutil, tempfile

print('=== END-TO-END GUI SIMULATION ===')
print()

# ====== 1. 模拟"查询分支" ======
print('1. 查询分支 (ls-remote)')
ssh = 'git@github.com:lindtkai/fpga_capability.git'
https = 'https://github.com/lindtkai/fpga_capability.git'
t0 = time.time()
# 先试 SSH, 失败试 HTTPS
for url in (ssh, https):
    try:
        r = subprocess.run(['git','ls-remote','--heads',url],
            capture_output=True, text=True, timeout=15,
            env=dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never'))
        if r.returncode == 0:
            branches = [l.split('\t')[-1].replace('refs/heads/','') for l in r.stdout.strip().split('\n') if 'refs/heads/' in l]
            print(f'  OK: {url[:50]} -> {len(branches)} branches ({branches})')
            print(f'  Time: {time.time()-t0:.1f}s')
            break
    except subprocess.TimeoutExpired:
        print(f'  TIMEOUT: {url[:50]}')
else:
    print('  FAIL: both protocols failed')
    sys.exit(1)

# ====== 2. 模拟"提交+推送" ======
print()
print('2. 提交 + 推送')
p = r'C:\Users\lindt\Desktop\test\tool'

# 写测试文件
test_file = os.path.join(p, 'test_gui_auto.txt')
with open(test_file, 'w', encoding='utf-8') as f:
    f.write(f'GUI e2e test at {time.ctime()}\n')

# git add
r = subprocess.run(['git','add',os.path.basename(test_file)], capture_output=True, text=True, cwd=p, timeout=10)
print(f'  git add: rc={r.returncode}')

# git commit
r = subprocess.run(['git','commit','-m','[GUI-e2e] auto test'], capture_output=True, text=True, cwd=p, timeout=10)
print(f'  git commit: rc={r.returncode}')
print(f'    {r.stdout.strip()[:120]}')

# set remote + push
subprocess.run(['git','remote','set-url','origin',url], capture_output=True, text=True, cwd=p, timeout=5)
branch = subprocess.run(['git','branch','--show-current'], capture_output=True, text=True, cwd=p, timeout=5).stdout.strip()
print(f'  push {branch} -> origin...')
r = subprocess.run(['git','push','-u','origin',branch], capture_output=True, text=True, cwd=p, timeout=30,
    env=dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never'))
ok = r.returncode == 0 or 'up-to-date' in (r.stderr+r.stdout).lower()
print(f'  push: rc={r.returncode} ok={ok}')
if r.stdout.strip(): print(f'    stdout: {r.stdout.strip()[:150]}')
if r.stderr.strip(): print(f'    stderr: {r.stderr.strip()[:150]}')
assert ok, 'PUSH FAILED'

# ====== 3. 模拟"删除仓库文件" (clone -> ls-files) ======
print()
print('3. 删除仓库文件 (clone + ls-files)')
tmp = tempfile.mkdtemp(prefix='test_del_')
r = subprocess.run(['git','clone','--depth=1','--single-branch','-b','main',url,tmp],
    capture_output=True, text=True, timeout=60,
    env=dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never'))
print(f'  clone main: rc={r.returncode}')
assert r.returncode == 0, f'CLONE FAILED: {(r.stderr or "")[:120]}'

r = subprocess.run(['git','-C',tmp,'ls-files'], capture_output=True, text=True, timeout=10)
files = [f for f in r.stdout.strip().split('\n') if f]
print(f'  files: {len(files)}')
shutil.rmtree(tmp, ignore_errors=True)

# ====== 4. 模拟"删除分支" ======
print()
print('4. 删除远程分支')
test_branch = f'gui-test-{int(time.time())%10000}'
# 创建 - 直接用 SSH URL 避免 HTTPS 不稳定
env_ssh = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never',
    GIT_SSH_COMMAND='ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8')
subprocess.run(['git','remote','set-url','origin','git@github.com:lindtkai/fpga_capability.git'],
    capture_output=True, text=True, cwd=p, timeout=5)
r = subprocess.run(['git','checkout','-b',test_branch], capture_output=True, text=True, cwd=p, timeout=10)
print(f'  checkout -b: rc={r.returncode}')
if r.returncode != 0:
    r = subprocess.run(['git','checkout','-f','-b',test_branch], capture_output=True, text=True, cwd=p, timeout=10)
    print(f'  checkout -f -b: rc={r.returncode}')
r = subprocess.run(['git','push','-u','origin',test_branch], capture_output=True, text=True, cwd=p, timeout=30, env=env_ssh)
print(f'  创建 {test_branch}: rc={r.returncode}')
assert r.returncode == 0, f'CREATE BRANCH FAILED: {(r.stderr or "")[:120]}'

# 删除 - env_ssh 在上面定义过了
r = subprocess.run(['git','push','origin','--delete',test_branch], capture_output=True, text=True, timeout=30, env=env_ssh)
ok = r.returncode == 0 or 'deleted' in (r.stderr+r.stdout).lower()
print(f'  删除 {test_branch}: rc={r.returncode} ok={ok}')
assert ok, f'DELETE BRANCH FAILED: {(r.stderr or "")[:120]}'

# 清理本地
subprocess.run(['git','checkout',branch], capture_output=True, text=True, cwd=p, timeout=10)
subprocess.run(['git','branch','-d',test_branch], capture_output=True, text=True, cwd=p, timeout=10)

print()
print('=== ALL 4 TESTS PASSED ===')
