# Provenance — Fermion: Mirai kara no Houmonsha (フェルミオン ～未来からの訪問者～)

- **Title**: Fermion - Mirai kara no Houmonsha
- **Publisher**: シルキーズ (Silky's)
- **Platform**: NEC PC-9801 (PC-98)
- **Release**: 1995-12-22
- **Media**: 4 × 5.25" HD floppy disks (Disks A–D)

## Source of record

`artifacts/` contains the preservation dump from archive.org item
[`fermion`](https://archive.org/details/fermion) (collections: flux-dumps,
softwarelibrary, emulation):

> 5.25" floppy disk images (Greaseweazle F1) for NEC PC-9801

Links:

- Item page: <https://archive.org/details/fermion>
- Download: <https://archive.org/download/fermion/Fermion%20-%20Mirai%20kara%20no%20Houmonsha%20%28Silky%27s%29%20%281995-12-22%29%20%5BPC98%5D%20%5B5.25%27%27%5D%20%5BSCP%2BMFI%2BHFE%2BD88%5D.zip>
- Storage node (used at fetch time): <https://ia801606.us.archive.org/15/items/fermion/Fermion%20-%20Mirai%20kara%20no%20Houmonsha%20%28Silky%27s%29%20%281995-12-22%29%20%5BPC98%5D%20%5B5.25%27%27%5D%20%5BSCP%2BMFI%2BHFE%2BD88%5D.zip>
- Torrent: <https://archive.org/download/fermion/fermion_archive.torrent>
- Item metadata (local copy: `archive-org-metadata.json`): <https://archive.org/metadata/fermion>

Each disk is provided in four formats:

| Format | Type | Use |
|--------|------|-----|
| `.scp` | SuperCard Pro flux stream | archival flux capture |
| `.mfi` | MAME flux image | archival flux capture |
| `.hfe` | HxC floppy emulator image | hardware/emulator use |
| `.d88` | sector image | emulator use, conversion source |

### Download integrity

Zip `Fermion - Mirai kara no Houmonsha (Silky's) (1995-12-22) [PC98] [5.25''] [SCP+MFI+HFE+D88].zip`

- size: 71285163 bytes
- sha1: `889c545fe29370075c1ca1f49118b180b7fc83ff` (matches archive.org
  metadata, see `archive-org-metadata.json`)
- sha256: `e59bd9e53b09ead22cd6eb73ceb122a5123b8cf4f90bf2e31591d7f82368d221`

Note: `https://archive.org/download/fermion/...` returned HTTP 500 at fetch
time; the file was fetched from the storage node URL
`https://ia801606.us.archive.org/15/items/fermion/...` recorded in the item
metadata.

## Content verification against MAME software list

The D88 images were converted to raw HDM sector images
(77 cyl × 2 head × 8 sec × 1024 B = 1261568 bytes, sectors reordered by
C/H/R) and their SHA-1 digests compared against the MAME `pc98` software
list entry `fermion` (snapshot in `mame-pc98-softwarelist-fermion.xml`,
upstream: [`hash/pc98.xml` in mamedev/mame](https://github.com/mamedev/mame/blob/master/hash/pc98.xml)).

All four disks match byte-for-byte:

| Disk | SHA-1 (HDM) | MAME CRC32 |
|------|-------------|------------|
| A | `b5af3375766b6a685c5f51bd7d1289f0d0fd38ad` | `847badeb` |
| B | `8a62c5191d1f093793e75e29d0595427bfa0caf8` | `13b70644` |
| C | `6d252df7645d9357a9d2d258fa983382583d9d2e` | `c4cf042b` |
| D | `b5e38ad283b79cff0605152f3de6f53e0baf8379` | `313e6603` |

## Working images

Working HDM images and any installed HDD image derived from these floppies
are build artifacts: regenerate them from `artifacts/` and do not commit
them. The expected pristine SHA-1 values are the MAME hashes above.
