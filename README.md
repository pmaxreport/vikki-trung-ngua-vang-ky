# Vikki × PMAX — Live Dashboard (GitHub Pages + Actions)

Site tĩnh tự cập nhật ~30 phút/lần. GitHub Actions đọc Google Sheet (FB_PAXY/TT_PAXY)
bằng OAuth → sinh `data.json` → commit → GitHub Pages hiển thị.

## Cấu trúc
- `index.html` — dashboard (fetch `./data.json`)
- `data.json` — dữ liệu (Actions tự sinh)
- `build_data.py` — đọc sheet + tổng hợp
- `requirements.txt` — thư viện Python
- `.github/workflows/update.yml` — lịch chạy ~30'
- `get_refresh_token.py` — CHẠY 1 LẦN Ở MÁY để lấy token (không bắt buộc đưa lên repo)

## Cài đặt (1 lần)
1. Google Cloud: bật **Google Sheets API**; OAuth consent = **Internal**; tạo OAuth client **Desktop app** → tải `client_secret.json`.
2. Ở máy: `pip install google-auth-oauthlib` rồi `python get_refresh_token.py` → copy 3 giá trị in ra.
3. GitHub → Settings → Secrets and variables → Actions → thêm 3 secret:
   `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`.
4. Settings → Pages → Deploy from branch `main` / root.
5. Tab Actions → "Update dashboard data" → Run workflow (chạy thử).

## Cập nhật ngay
Actions → Run workflow. (Lịch tự động ~30' là best-effort, có thể trễ 5–30').

## Sửa giao diện
Thay `index.html` mới → không đụng phần còn lại.
