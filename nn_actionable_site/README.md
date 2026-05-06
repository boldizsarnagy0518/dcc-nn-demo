# NN Biztosító döntéstámogató mini oldal

Kattintható, statikus mini weboldal az NN ügyfeleknek szóló döntéstámogató élmény bemutatására.

## Mit mutat

- Nyugdíj/SZJA kalkulátor.
- Életbiztosítási fedezetbecslő.
- Egészség Útlevél döntéstámogató.
- Használható kalkulátorok, közérthető magyarázatokkal és NN következő lépésekkel.
- Meta title, description, OG description és egyszerű JSON-LD blokk.

## Miért külön ez a demo

Ez nem a meglévő POC dashboard helyettesítése. A dashboard a controlled validation evidence.
Ez a mappa a QR-kóddal nyitható, user-facing demonstráció: megmutatja, milyen oldalelemekkel lehetne az NN oldalán konkrétabb, könnyebben használható döntéstámogatást adni.

## Lokális megnyitás

Nyisd meg ezt a fájlt böngészőben:

```text
nn_actionable_site/index.html
```

## Vercel

Statikus site, build step nélkül.

Két biztonságos opció van:

1. A teljes repo deployolása Vercelen. Ehhez a repo rootban lévő `vercel.json` a `/` útvonalat erre a mappára irányítja.
2. Csak az `nn_actionable_site` mappa deployolása külön Vercel projektként. Ebben az esetben nincs szükség build parancsra vagy output directoryra.

QR-kódhoz a deploy után kapott Vercel URL gyökere használható, például:

```text
https://<project-name>.vercel.app/
```
