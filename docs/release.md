# Release Checklist

1. Run deterministic QA:

   ```powershell
   .\scripts\qa.ps1
   ```

2. Run live Ollama evaluation when models are available:

   ```powershell
   python scripts/evaluate.py --strict-ocr
   ```

3. Build the wheel:

   ```powershell
   Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
   python -m pip wheel . --no-deps -w dist
   ```

4. Inspect wheel metadata:

   ```powershell
   python -c "import pathlib, zipfile; w=next(pathlib.Path('dist').glob('*.whl')); print(w); print('\n'.join(zipfile.ZipFile(w).namelist()))"
   ```

5. Create the public GitHub repository, then push:

   ```powershell
   git remote add origin https://github.com/YehudRaanan/photo-vlm-mcp.git
   git push -u origin main
   ```

6. After publication, update `pyproject.toml` URLs if the final owner/name differs.
