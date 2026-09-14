from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]

def frontmatter(path:Path)->dict[str,str]:
    text=path.read_text(encoding='utf-8'); m=re.match(r'^---\n(.*?)\n---\n',text,re.S); assert m
    out={}
    for line in m.group(1).splitlines():
        k,v=line.split(':',1); out[k.strip()]=v.strip()
    return out

def test_dev_skill_structure():
    root=ROOT/'skills/sponsor-job-agent-dev'; fm=frontmatter(root/'SKILL.md')
    assert fm['name']=='sponsor-job-agent-dev'; assert fm['description'].startswith('Use when')
    for f in ['architecture.md','backend-boundaries.md','frontend-contracts.md','immigration-engine.md','testing.md']:
        assert (root/'references'/f).exists()

def test_ops_skill_structure_and_manual_stop():
    root=ROOT/'skills/sponsor-job-agent-ops'; fm=frontmatter(root/'SKILL.md')
    assert fm['name']=='sponsor-job-agent-ops'; assert fm['description'].startswith('Use when')
    text=(root/'SKILL.md').read_text(); assert 'ready_to_submit' in text and 'final Submit' in text
    for f in ['daily-workflow.md','application-safety.md','visa-answer-rules.md']:
        assert (root/'references'/f).exists()

def test_skill_trees_contain_no_private_paths_or_candidate_files():
    forbidden={'config/local','.env','jobs.db','browser_profiles'}
    for root in [ROOT/'skills/sponsor-job-agent-dev',ROOT/'skills/sponsor-job-agent-ops']:
        for p in root.rglob('*'):
            rel=p.relative_to(root).as_posix()
            assert not any(x in rel for x in forbidden)
            assert p.suffix.lower() not in {'.pdf','.docx'}
