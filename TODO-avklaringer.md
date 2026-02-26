# Avklaringer som trengs

Spørsmål som må besvares før vi kan lage detaljert design og begynne å kode.

## A. Eksisterende anlegg

- [ ] **Varmepumpe**: Hvilken type/modell? Har den eget styringssystem i dag?
- [ ] **Styring i dag**: Hvordan styres pumpen nå — enkel av/på, eller modulerende effekt?
- [ ] **Relébehov**: Er det enkel av/på (230V kontaktor), eller kreves kommunikasjon (Modbus, RS485, etc.)?
- [ ] **Sirkulasjonspumpe**: Egen pumpe i bakkeløyfen, eller drives den av varmepumpen?
- [ ] **Areal**: Hvor stort areal dekker bakkeløyfen?
- [ ] **Treghet**: Hvor lang tid fra oppstart til bakken er varm — minutter eller timer?
- [ ] **Eksisterende sensorer**: Finnes det allerede temperaturfølere i systemet (tur/retur)?

## B. Infrastruktur på stedet

- [ ] **Strøm**: Har RPi tilgang til strøm der den skal monteres?
- [ ] **Nettverk**: WiFi eller Ethernet tilgjengelig?
- [ ] **Plassering**: Innendørs (teknisk rom) eller utendørs (kapsling nødvendig)?

## C. Prediktiv logikk

- [ ] **Treghet i systemet**: Nøyaktig tidsforsinkelse fra oppstart til effekt (avgjør hvor langt frem vi må predikere)
- [ ] **Temperaturgrenser**: Hvilket område er "farlig"? (typisk 0 til -5 grader C med fukt)
- [ ] **Prioritet**: Optimalisere for energibruk eller for 100% sikkerhet mot is?

## D. Funksjonelle ønsker

- [ ] **Varsling**: Ønskes varsling på mobil (SMS/push) ved oppstart, feil, etc.?
- [ ] **Fjernstyring**: Skal systemet kunne styres fra utenfor lokalt nett?
- [ ] **Logging**: Hvor lenge skal historikk lagres?
- [ ] **Integrasjoner**: Ønskes integrasjon med smarthus (Home Assistant, etc.)?
