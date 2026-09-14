from __future__ import annotations
import re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SKIP_DIRS={'.git','.venv','venv','node_modules','.next','dist','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache'}
FORBIDDEN_PATH_PARTS={'config/local','browser_profiles','artifacts'}
SECRET_PATTERNS={
 'openai-key': re.compile(r'\bsk-[A-Za-z0-9_-]{20,}\b'),
 'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
 'github-token': re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}\b'),
}
AUTO_SUBMIT=[
 re.compile(r'page\.(?:click|locator)\([^\n]{0,120}submit[^\n]{0,120}\)\.?(?:click\(\))?',re.I),
 re.compile(r'locator\([^\n]{0,120}submit[^\n]{0,120}\)\.click\(',re.I),
]
TEXT_EXT={'.py','.ts','.tsx','.js','.mjs','.json','.md','.yml','.yaml','.toml','.ini','.sh','.ps1','.txt','.css'}

def scan(root:Path=ROOT)->list[tuple[str,str]]:
    findings=[]
    for path in root.rglob('*'):
        if any(part in SKIP_DIRS for part in path.parts): continue
        if not path.is_file(): continue
        rel=path.relative_to(root).as_posix()
        if rel=='.env' or (rel.startswith('data/') and path.suffix=='.db') or any(x in rel for x in FORBIDDEN_PATH_PARTS): findings.append((rel,'forbidden-path'))
        if path.suffix.lower() in {'.pdf','.docx'} and not rel.startswith('tests/fixtures/'): findings.append((rel,'candidate-document'))
        if path.suffix.lower() not in TEXT_EXT and path.name not in {'.env','.env.example','.gitignore'}: continue
        try: text=path.read_text(encoding='utf-8')
        except UnicodeDecodeError: continue
        for name,pat in SECRET_PATTERNS.items():
            if pat.search(text): findings.append((rel,name))
        if rel.startswith(('src/','apps/web/')):
            for pat in AUTO_SUBMIT:
                if pat.search(text): findings.append((rel,'final-submit-action'))
    return sorted(set(findings))

def main()->int:
    findings=scan()
    if findings:
        for path,rule in findings: print(f'{path}: {rule}',file=sys.stderr)
        return 1
    print('Public repository scan OK')
    return 0
if __name__=='__main__': raise SystemExit(main())
