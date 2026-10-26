-- ============================================================================
-- Migrasi koreksi data #2 — dijalankan di environment development 2026-10-01,
-- PERLU DIJALANKAN ULANG MANUAL di database produksi asli (server ini terpisah
-- dari produksi). Jalankan SATU-PER-SATU sambil cek hasilnya, JANGAN sekaligus
-- tanpa lihat — dan WAJIB backup database produksi dulu sebelum menjalankan ini.
--
-- Lihat juga migrasi_koreksi_data_2026-09-20.sql (koreksi #1, topik berbeda:
-- normalisasi nama dokter & komisi Natalia). File ini topik baru: data legacy
-- Stok_barang yg rusak sejak migrasi dari Access dulu (migrate_access.py).
-- ============================================================================

-- ── Latar belakang (temuan 2026-09-29/10-01) ──────────────────────────────
-- Ditemukan 15 kd_barang (semua SUDAH MATI — stok_sisa=0 di SEMUA batch-nya,
-- tidak terdaftar di master Barang, nol jejak di RiwayatBarang/Transfer_Stok_Log)
-- yg kolom `satuan`-nya kebetulan berisi ANGKA (bukan teks satuan spt 'gr'/'pcs'),
-- dan kolom `disc`-nya berisi angka >100% (mustahil sbg persentase diskon — kalau
-- barang ini pernah dijual, rumus `harga*(1-disc/100)` akan menghasilkan harga
-- NEGATIF). Root cause: migrate_access.py (skrip migrasi CSV dari Access, 1x
-- dijalankan dulu) menyalin kolom `satuan`/`disc` mentah2 dari CSV TANPA validasi,
-- dan tabel Stok_barang memang tidak dicatat ke RiwayatBarang saat diimpor —
-- jadi nilai yg sudah salah sejak di sistem LAMA ikut terbawa tanpa jejak.
--
-- Di dev: 108 baris satuan dikosongkan, 103 baris disc direset ke 0 (94 baris
-- kena KEDUANYA, jadi total 15 kd_barang unik terdampak — lihat MEMORY.md /
-- memory 'koreksi-data-satuan-disc-legacy' utk daftar lengkap nama barangnya).

-- 1) CEK DULU sebelum eksekusi — lihat berapa baris yg match pola ini di
--    produksi (SEHARUSNYA 0 yg stok_sisa>0; kalau ada yg stok_sisa>0, JANGAN
--    lanjut UPDATE dulu — barang itu AKTIF, perlu dicek manual, bukan auto-fix):
SELECT id, kd_barang, nm_barang, harga, disc, satuan, stok_sisa
FROM Stok_barang
WHERE satuan REGEXP '^[0-9]+(\\.[0-9]+)?$'
   OR CAST(disc AS DECIMAL(10,2)) > 100;

-- 2) Kosongkan `satuan` yg isinya angka murni (bukan teks satuan) — HANYA utk
--    baris yg stok_sisa=0 (pengaman: barang mati, tidak sedang dijual). Kalau
--    langkah (1) di atas menunjukkan ada yg stok_sisa>0, TAMBAHKAN dulu
--    AND stok_sisa=0 ini sudah benar scope-nya — jangan dihapus, supaya barang
--    yg masih aktif tidak ikut tersentuh tanpa review manual.
UPDATE Stok_barang
SET satuan = ''
WHERE stok_sisa = 0
  AND satuan REGEXP '^[0-9]+(\\.[0-9]+)?$';

-- 3) Reset `disc` yg >100% (mustahil sbg persentase) ke '0' — sama, HANYA
--    utk stok_sisa=0.
UPDATE Stok_barang
SET disc = '0'
WHERE stok_sisa = 0
  AND CAST(disc AS DECIMAL(10,2)) > 100;

-- ============================================================================
-- Verifikasi setelah selesai (jalankan, harus kembalikan 0 baris):
--   SELECT COUNT(*) FROM Stok_barang
--     WHERE satuan REGEXP '^[0-9]+(\\.[0-9]+)?$' OR CAST(disc AS DECIMAL(10,2)) > 100;
-- ============================================================================

-- ============================================================================
-- SUSULAN 2026-10-01 (v2) — PENTING, baca sebelum jalankan langkah (2) di atas:
--
-- Saat dijalankan ulang di dev (data sempat di-restore/diganti user), ketemu
-- SATU baris (kd_barang 'Zalp Kloderma Gel gr') yg kena bug ini TAPI MASIH
-- BERSTOK AKTIF (stok_sisa>0, exp di masa depan — bukan lagi barang mati). Kalau
-- baris spt ini langsung dikosongkan `satuan`-nya tanpa cek, jadinya 'satuan
-- kosong' utk barang yg AKTIF dijual — kurang ideal. Barang ini KEBETULAN sudah
-- terdaftar di master Barang dgn `satuan='Pcs'` yg BENAR, jadi lebih baik
-- pakai itu sbg pengganti drpd dikosongkan.
--
-- JADI: sebelum jalankan UPDATE (2), CEK DULU tiap kd_barang yg match pola bug
-- di produksi (dari hasil SELECT langkah 1) satu-per-satu:
--   SELECT satuan FROM Barang WHERE kd_barang = '<kd_barang_yg_bermasalah>';
-- - Kalau TERDAFTAR & satuan-nya masuk akal → pakai UPDATE manual per-barang ini
--   (bukan langkah 2 yg generik):
--     UPDATE Stok_barang SET satuan = '<satuan_dari_master>'
--     WHERE kd_barang = '<kd_barang_yg_bermasalah>'
--       AND satuan REGEXP '^[0-9]+(\\.[0-9]+)?$';
-- - Kalau TIDAK terdaftar (kasus normal, mayoritas) → langkah (2) generik di
--   atas (dikosongkan) sudah cukup aman, apalagi kalau stok_sisa=0 semua.
--
-- Langkah (3) [reset disc>100 ke 0] TETAP AMAN dijalankan generik ke SEMUA
-- baris tanpa pengecualian — disc selalu '0' adalah nilai aman apa pun kondisi
-- stoknya (tidak pernah salah/merugikan drpd membiarkan disc mustahil >100%
-- yg bisa bikin harga jual NEGATIF kalau barang itu sempat terjual).
-- ============================================================================
