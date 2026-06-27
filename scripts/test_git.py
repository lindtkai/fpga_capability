"""Git Tab 自动化自测 - 直接调用 gen_gui 核心函数"""
import sys, os, subprocess, time, shutil, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import gen_gui  # 猴子补丁生效

failed = []
p = r'C:\Users\lindt\Desktop\test\tool'
ssh = 'git@github.com:lindtkai/fpga_capability.git'
https = 'https://github.com/lindtkai/fpga_capability.git'

def test(name, func):
    try:
        func()
        print(f'  [PASS] {name}')
    except Exception as e:
        print(f'  [FAIL] {name}: {e}')
        failed.append(name)

def check(cond, name):
    if not cond:
        raise AssertionError(name)

# ===== 1. URL SSH<->HTTPS 互转 =====
print('1. URL SSH/HTTPS 互转')
s, h = gen_gui._url_to_ssh_and_https(ssh)
test('SSH->HTTPS github.com', lambda: check('github.com' in h, h))
s_val, _ = gen_gui._url_to_ssh_and_https(https)
test('HTTPS->SSH git@', lambda: check('git@' in s_val, s_val))

# ===== 2. 连通性并行检测 =====
print('2. _detect_reachable_url 并行检测')
t0 = time.time()
best, proto = gen_gui._detect_reachable_url(ssh, https)
dt = time.time() - t0
print(f'   耗时 {dt:.1f}s, 结果: {best} ({proto})')
test('耗时 < 15s', lambda: check(dt < 15, f'{dt}s > 15s'))
test('至少一条路通', lambda: check(best is not None, 'both failed'))

# ===== 3. ls-remote 查询分支 =====
print('3. git ls-remote 查询分支')
env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never')
if proto == 'ssh':
    env['GIT_SSH_COMMAND'] = 'ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8'
r = subprocess.run(['git','ls-remote','--heads',best], capture_output=True, text=True, timeout=15, env=env)
test('ls-remote 成功', lambda: check(r.returncode == 0, (r.stderr or 'fail')[:80]))
branches = []
for line in r.stdout.strip().split('\n'):
    if 'refs/heads/' in line:
        branches.append(line.split('refs/heads/')[-1].strip())
print(f'   分支: {branches}')
test('有分支列表', lambda: check(len(branches) > 0, 'no branches'))

# ===== 4. commit + push =====
print('4. git commit + push')
# 确保仓库存在
if not os.path.isdir(os.path.join(p, '.git')):
    subprocess.run(['git','init'], cwd=p)
    subprocess.run(['git','remote','add','origin',best], cwd=p)
# 写测试文件
with open(os.path.join(p, 'test_auto.txt'), 'w', encoding='utf-8') as f:
    f.write(f'auto test {time.ctime()}\n')
r = subprocess.run(['git','add','test_auto.txt'], capture_output=True, text=True, cwd=p, timeout=10)
r = subprocess.run(['git','commit','-m','[auto-test] ci'], capture_output=True, text=True, cwd=p, timeout=10)
test('git commit 成功', lambda: check(r.returncode == 0, (r.stderr or '')[:80]))
# push
branch = subprocess.run(['git','branch','--show-current'], capture_output=True, text=True, cwd=p, timeout=5).stdout.strip()
subprocess.run(['git','remote','set-url','origin',best], capture_output=True, text=True, cwd=p, timeout=5)
r = subprocess.run(['git','push','-u','origin',branch], capture_output=True, text=True, cwd=p, timeout=30, env=env)
push_ok = r.returncode == 0 or 'up-to-date' in (r.stderr + r.stdout).lower()
test('git push 成功', lambda: check(push_ok, (r.stderr or r.stdout)[:120]))
print(f'   stdout: {r.stdout.strip()[:100]}')
print(f'   stderr: {r.stderr.strip()[:100]}')

# ===== 5. clone 测试 =====
print('5. git clone (模拟删除仓库文件的前半段)')
tmp = tempfile.mkdtemp(prefix='test_clone_')
r = subprocess.run(['git','clone','--depth=1','--single-branch','-b','main',best,tmp],
    capture_output=True, text=True, timeout=60, env=dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never'))
test('clone main 成功', lambda: check(r.returncode == 0, (r.stderr or '')[:80]))
shutil.rmtree(tmp, ignore_errors=True)

# ===== 6. push --delete =====
print('6. git push --delete (删除远程分支)')
test_branch = f'auto-test-{int(time.time()) % 10000}'
r = subprocess.run(['git','checkout','-b',test_branch], capture_output=True, text=True, cwd=p, timeout=10)
r = subprocess.run(['git','push','-u','origin',test_branch], capture_output=True, text=True, cwd=p, timeout=30, env=env)
test(f'创建测试分支 {test_branch}', lambda: check(r.returncode == 0, (r.stderr or '')[:80]))
r = subprocess.run(['git','push','origin','--delete',test_branch], capture_output=True, text=True, timeout=30, env=env)
del_ok = r.returncode == 0 or 'deleted' in (r.stderr + r.stdout).lower()
test(f'删除分支 {test_branch}', lambda: check(del_ok, (r.stderr or '')[:80]))
# 清理本地
subprocess.run(['git','checkout',branch], capture_output=True, text=True, cwd=p, timeout=10)
subprocess.run(['git','branch','-d',test_branch], capture_output=True, text=True, cwd=p, timeout=10)

# ===== 结果 =====
print()
print(f'总测试: 6大类, 失败: {len(failed)}')
if failed:
    for f in failed:
        print(f'  FAILED: {f}')
else:
    print('=== ALL TESTS PASSED ===')
