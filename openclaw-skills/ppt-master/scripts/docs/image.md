# Image Tools

## Runtime AI image tasks

PPT Master does not include an AI provider backend. Use `image_manifest.py` to validate prompts, expose stable runtime arguments, record returned files, and verify assets:

```bash
python3 {baseDir}/scripts/image_manifest.py check <project>/images/image_prompts.json
python3 {baseDir}/scripts/image_manifest.py pending <project>/images/image_prompts.json
python3 {baseDir}/scripts/image_manifest.py record <manifest> <filename> --source <returned-file>
python3 {baseDir}/scripts/image_manifest.py verify <project>/images/image_prompts.json
```

See [`../../references/runtime-media.md`](../../references/runtime-media.md) and [`../../references/image-generator.md`](../../references/image-generator.md).

## Formula rendering

```bash
python3 {baseDir}/scripts/latex_render.py <absolute-project>
python3 {baseDir}/scripts/latex_render.py <absolute-project> --providers codecogs,quicklatex,mathpad,wikimedia
```

Formula files land under the project's `images/` directory. The provider chain is specific to deterministic formula rendering and is not the AI image-provider contract.

## Web image search

```bash
python3 {baseDir}/scripts/image_search.py "<query>" --filename <name.jpg> --output-dir <absolute-project>/images
python3 {baseDir}/scripts/image_search.py --batch <absolute-project>/images/image_queries.json
```

Openverse and Wikimedia work without keys. Optional `PEXELS_API_KEY` and `PIXABAY_API_KEY` broaden stock-photo coverage. License/provenance rules are in [`../../references/image-searcher.md`](../../references/image-searcher.md).

## Analysis and local processing

```bash
python3 {baseDir}/scripts/analyze_images.py <absolute-project>/images
python3 {baseDir}/scripts/slice_images.py <sheet.png> --grid 2x2 --names a,b,c,d --trim --alpha
python3 {baseDir}/scripts/rotate_images.py gen <absolute-project>/images
```
