from pathlib import Path
import os,subprocess,tempfile,shutil
root=Path.cwd(); source=root/'web/src/desk/chair/ChairHome.tsx'; original=source.read_bytes()
out=root/'pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/verification'
env=os.environ.copy(); env['HOME']=tempfile.mkdtemp(prefix='philo504-c3-test-'); env['PATH']='/Users/karol/.nvm/versions/node/v22.21.0/bin:'+env['PATH']
old='.catch((error) => setBriefLoadFailed(briefLoadCause(error)))'
assert original.decode().count(old)==1
try:
 source.write_text(original.decode().replace(old,'.catch((error) => { setBriefKept(null); setBriefLoadFailed(briefLoadCause(error)); })'))
 result=subprocess.run(['npx','vitest','run','--maxWorkers=2','src/desk/chair/__tests__/briefFreshRead.philo504.test.tsx'],cwd=root/'web',env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (out/'c3-clear-on-failure-mutation.txt').write_text(result.stdout)
 print(result.stdout)
 assert result.returncode==1 and 'retains the first receipt' in result.stdout
 print('EXPECTED REJECTION: clearing an existing receipt on read failure fails the rendered C3 fence')
finally:
 source.write_bytes(original)
assert source.read_bytes()==original
print('Original product file restored by this explicit path; byte equality verified.')
