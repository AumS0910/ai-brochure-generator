# Asset Upload (V2.2 Backend)

## Hero Upload
```bash
curl -X POST "http://localhost:8000/brochures/<id>/assets/hero" \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@C:\\path\\to\\hero.jpg"
```

Expected:
- `hero_user.png` saved in `backend/output/runs/<id>/`
- Schema updated with `assets.hero_image.source = user`
- PNG/PDF re-rendered

## Gallery Upload (max 5)
```bash
curl -X POST "http://localhost:8000/brochures/<id>/assets/gallery" \
  -H "Authorization: Bearer <TOKEN>" \
  -F "files=@C:\\path\\to\\img1.jpg" \
  -F "files=@C:\\path\\to\\img2.jpg"
```

Expected:
- `gallery_1.png...gallery_n.png` saved in `backend/output/runs/<id>/`
- Schema `assets.gallery[]` appended
- PNG/PDF re-rendered
