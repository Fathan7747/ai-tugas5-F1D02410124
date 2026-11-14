"""Sistem pakar sederhana: diagnosis gangguan Wi-Fi pada laptop.

Metode : Forward Chaining (mesin inferensi ditulis sendiri, tanpa library).
Aturan : dibaca dari kb_wifi.json.

Cara pakai:
    python main.py                      -> mode tanya jawab (y/t)
    python main.py --ya "fakta" "fakta" -> fakta langsung diberikan (untuk uji)
"""
import argparse
import json
import sys

FILE_KB = "kb_wifi.json"


def muat_kb(path):
    """Baca file aturan JSON."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fakta_dasar(kb):
    """Fakta yang harus ditanyakan: muncul di bagian JIKA tapi tidak pernah
    menjadi hasil (MAKA) dari aturan mana pun. Urutan sesuai kemunculan."""
    hasil = {r["maka"] for r in kb["aturan"]}
    urut = []
    for r in kb["aturan"]:
        for k in r["jika"]:
            if k not in hasil and k not in urut:
                urut.append(k)
    return urut


def terpenuhi(aturan, memori):
    """Mode 'dan' = semua syarat ada di memori, 'atau' = salah satu cukup."""
    ada = [k in memori for k in aturan["jika"]]
    return all(ada) if aturan["mode"] == "dan" else any(ada)


def forward_chaining(kb, fakta_awal):
    """Jalankan aturan berulang sampai tidak ada aturan baru yang bisa dipakai.

    Mengembalikan:
      memori : semua fakta (awal + hasil inferensi)
      asal   : {hasil: (aturan, syarat yang benar-benar dipakai)} untuk alasan
      siklus : daftar aturan sesuai urutan dijalankan
    """
    memori = set(fakta_awal)
    asal = {}
    siklus = []
    while True:
        # aturan yang syaratnya terpenuhi DAN hasilnya belum ada di memori
        # (kalau tidak, program tidak akan pernah berhenti)
        cocok = [r for r in kb["aturan"]
                 if r["maka"] not in memori and terpenuhi(r, memori)]
        if not cocok:
            break
        r = cocok[0]                                   # ambil aturan pertama
        syarat = [k for k in r["jika"] if k in memori]  # syarat yang dipakai
        memori.add(r["maka"])
        asal[r["maka"]] = (r, syarat)
        siklus.append(r)
    return memori, asal, siklus


def tampilkan_alasan(fakta, asal, indent=0):
    """Cetak alasan secara rekursif: kesimpulan <- aturan (syarat) [sumber]."""
    r, syarat = asal[fakta]
    print(" " * indent + f"{fakta}  <- {r['id']} ({', '.join(syarat)}) [{r['sumber']}]")
    for k in syarat:
        if k in asal:                       # syarat ini hasil aturan lain
            tampilkan_alasan(k, asal, indent + 4)


def tanya(pertanyaan):
    """Tanya y/t sampai jawabannya valid."""
    while True:
        try:
            j = input(f"{pertanyaan} (y/t) > ").strip().lower()
        except EOFError:
            sys.exit("\nInput berakhir.")
        if j in ("y", "t"):
            return j == "y"
        print("  Jawab dengan y atau t.")


def main():
    ap = argparse.ArgumentParser(description="Sistem pakar gangguan Wi-Fi (Forward Chaining)")
    ap.add_argument("--kb", default=FILE_KB, help="path file aturan JSON")
    ap.add_argument("--ya", nargs="*", help="daftar fakta yang dijawab ya (tanpa tanya jawab)")
    args = ap.parse_args()

    kb = muat_kb(args.kb)
    dasar = fakta_dasar(kb)

    print(kb["judul"])
    print("Jawab y/t.")

    fakta_awal = []
    if args.ya is not None:
        salah = [f for f in args.ya if f not in dasar]
        if salah:
            sys.exit("Fakta tidak dikenal: " + "; ".join(salah))
        for i, f in enumerate(dasar, 1):
            jawab = f in args.ya
            print(f"{i}. Apakah {f}? (y/t) > {'y' if jawab else 't'}")
            if jawab:
                fakta_awal.append(f)
    else:
        for i, f in enumerate(dasar, 1):
            if tanya(f"{i}. Apakah {f}?"):
                fakta_awal.append(f)

    print()
    print("Fakta awal: " + (", ".join(fakta_awal) if fakta_awal else "(tidak ada)"))
    print()

    memori, asal, siklus = forward_chaining(kb, fakta_awal)

    for n, r in enumerate(siklus, 1):
        print(f"Siklus {n}: {r['id']} -> {r['maka']}")
    print(f"Siklus {len(siklus) + 1}: tidak ada aturan baru, berhenti")
    print()

    # kesimpulan = hasil inferensi yang tidak dipakai sebagai syarat aturan lain
    dipakai = {k for _, syarat in asal.values() for k in syarat}
    kesimpulan = [r["maka"] for r in siklus if r["maka"] not in dipakai]

    if kesimpulan:
        print("Kesimpulan: " + ", ".join(kesimpulan))
        print("Alasan:")
        for k in kesimpulan:
            tampilkan_alasan(k, asal, indent=2)
    else:
        print("Kesimpulan: tidak ada kesimpulan yang bisa ditarik dari fakta tersebut.")

    print()
    terpakai = sorted({r["sumber"] for r in siklus})
    if terpakai:
        print("Sumber:")
        for s in terpakai:
            print(f"  {s}: {kb['sumber'][s]}")
        print()
    print("Catatan: " + kb["batas"])


if __name__ == "__main__":
    main()
