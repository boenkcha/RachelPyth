-- ============================================================================
-- Migrasi koreksi data — dijalankan di environment development 2026-09-19/20,
-- PERLU DIJALANKAN ULANG MANUAL di database produksi asli (server ini terpisah
-- dari produksi). Jalankan SATU-PER-SATU sambil cek hasilnya, JANGAN sekaligus
-- tanpa lihat — dan WAJIB backup database produksi dulu sebelum menjalankan ini
-- (pakai menu Backup di aplikasi, atau backup MySQL langsung / mysqldump).
--
-- Aman dijalankan ulang (idempotent) — kalau sudah pernah dijalankan, baris
-- kedua/ketiga tidak akan menemukan apa pun untuk diubah lagi (tidak merusak).
-- ============================================================================

-- 1) Normalisasi nama dokter di Penjualan.dokter: 'dr. Desidera' (teks bebas,
--    dropdown lama) -> 'DESIDERA HUSADANI Sp.KK' (konsisten dgn data Karyawan).
--    Dampak: 2 baris transaksi historis (kalau di produksi jumlahnya beda,
--    itu wajar — cuma menyesuaikan nama, bukan indikasi salah).
UPDATE Penjualan SET dokter='DESIDERA HUSADANI Sp.KK' WHERE dokter='dr. Desidera';

-- 2) Nonaktifkan 3 karyawan bertipe 'Dokter' yg bukan dokter asli/tidak
--    relevan lagi (DR.VIVIN, ucha, dr. RETA OKTASARI) — supaya tidak lagi
--    muncul di dropdown "Pilih Dokter" (Rekam Medik). Data historis TETAP
--    utuh (cuma dinonaktifkan, bukan dihapus).
UPDATE Karyawan SET aktif=0 WHERE kd_karyawan IN ('DOKTER', 'ucha', 'RETA');

-- 3) Gabungkan duplikat karyawan "Desidera": kd_karyawan 'desidera'
--    (DESIDERA HUSADANI Sp.KK, cuma py 1 baris riwayat komisi) digabung ke
--    'DA' (DR. DESIDERA HUSADANI Sp.KK, data utama — 222+ baris riwayat).
--    3a. Pindahkan SEMUA riwayat komisi dari 'desidera' ke 'DA':
UPDATE Point_karyawan SET kd_karyawan='DA' WHERE kd_karyawan='desidera';
--    3b. (Kalau ada, jaga-jaga tabel lain yg mungkin ikut mereferensikan —
--         di dev, semua ini kosong utk 'desidera', tapi jalankan juga jaga2)
UPDATE R_Penjualan       SET kd_karyawan='DA' WHERE kd_karyawan='desidera';
UPDATE Stok_Perawat      SET kd_karyawan='DA' WHERE kd_karyawan='desidera';
UPDATE Kit_Log           SET kd_karyawan='DA' WHERE kd_karyawan='desidera';
UPDATE Kit_Request       SET kd_karyawan='DA' WHERE kd_karyawan='desidera';
UPDATE Serah_Terima_Kunci SET kd_pelaksana='DA' WHERE kd_pelaksana='desidera';
UPDATE Serah_Terima_Kunci SET kd_k_dipilih='DA' WHERE kd_k_dipilih='desidera';
UPDATE Serah_Terima_Kunci SET kd_k_final='DA'   WHERE kd_k_final='desidera';
UPDATE Pengguna          SET kd_karyawan='DA' WHERE kd_karyawan='desidera';
--    3c. BARU setelah 3a/3b dijalankan & dicek tidak ada sisa riwayat,
--        hapus record duplikatnya:
--        CEK DULU (harus kosong semua sebelum lanjut ke DELETE):
--          SELECT * FROM Point_karyawan WHERE kd_karyawan='desidera';
--          SELECT * FROM R_Penjualan WHERE kd_karyawan='desidera';
--          SELECT * FROM Stok_Perawat WHERE kd_karyawan='desidera';
--          SELECT * FROM Kit_Log WHERE kd_karyawan='desidera';
--          SELECT * FROM Kit_Request WHERE kd_karyawan='desidera';
--          SELECT * FROM Serah_Terima_Kunci WHERE kd_pelaksana='desidera' OR kd_k_dipilih='desidera' OR kd_k_final='desidera';
--          SELECT * FROM Pengguna WHERE kd_karyawan='desidera';
DELETE FROM Karyawan WHERE kd_karyawan='desidera';

-- 4) Perbaiki field 'pekerjaan' DR. NATALIA WAHYUDI (kd_karyawan='NT') — tersimpan
--    literal 'Sp. KK' (itu title/gelarnya, BUKAN kategori peran yg dipakai sistem
--    utk dropdown "Pilih Dokter" & perhitungan tarif komisi). Ganti jadi 'Dokter'.
--    CEK DULU nilai kolom lain (nickname/telp/aktif) di produksi SAMA/beda dgn dev
--    sebelum menjalankan — kalau beda, sesuaikan UPDATE di bawah supaya kolom lain
--    TIDAK ikut tertimpa balik ke nilai dev:
--      SELECT * FROM Karyawan WHERE kd_karyawan='NT';
UPDATE Karyawan SET pekerjaan='Dokter' WHERE kd_karyawan='NT' AND pekerjaan='Sp. KK';

-- 4b. Lengkapi nama DR. NATALIA WAHYUDI dgn title (konsisten dgn cara nama dokter
--     lain ditulis, mis. "DR. DESIDERA HUSADANI Sp.KK").
UPDATE Karyawan SET nm_karyawan='DR. NATALIA WAHYUDI, Sp.KK'
  WHERE kd_karyawan='NT' AND nm_karyawan='DR. NATALIA WAHYUDI';

-- 5) Koreksi komisi DR. NATALIA WAHYUDI utk layanan "KONSULTASI dr. NATALIA"
--    (kd_pelayanan='KDN') — 657 baris di dev tercatat komisi Rp0 krn poin (4) di
--    atas belum diperbaiki saat baris2 itu dibuat (sistem kira dia bukan dokter),
--    padahal tarif komisi_dokter di produk_pelayanan utk layanan ini Rp200.000.
--    PENTING: cek dulu jumlah baris & nilai komisi SEBELUM update, supaya tidak
--    salah timpa kalau ternyata produksi datanya beda dari dev:
--      SELECT komisi, COUNT(*) FROM Point_karyawan
--        WHERE kd_karyawan='NT' AND kd_pelayanan='KDN' GROUP BY komisi;
--      -- di dev: semua 657 baris komisi=0 sebelum dikoreksi
UPDATE Point_karyawan SET komisi=200000
  WHERE kd_karyawan='NT' AND kd_pelayanan='KDN' AND komisi=0;

-- ============================================================================
-- Verifikasi setelah selesai (jalankan, harus sesuai catatan):
--   SELECT kd_karyawan, nm_karyawan, aktif FROM Karyawan WHERE pekerjaan='Dokter';
--     -> harus tersisa: ADM(1), DA(1), lk(1), RSL(1), NT(1), DOKTER(0), ucha(0), RETA(0)
--        dan 'desidera' SUDAH TIDAK ADA sama sekali.
--   SELECT COUNT(*) FROM Point_karyawan WHERE kd_karyawan='DA';
--     -> harus jumlah lama + 1 (baris yg dipindah dari 'desidera')
--   SELECT komisi, COUNT(*) FROM Point_karyawan
--     WHERE kd_karyawan='NT' AND kd_pelayanan='KDN' GROUP BY komisi;
--     -> harus SEMUA baris komisi=200000, tidak ada lagi yg 0
-- ============================================================================
