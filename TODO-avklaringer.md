# Avklaringer som trengs

Sporsmal som ma besvares for vi kan lage detaljert design og begynne a kode.

## A. Eksisterende anlegg

- [ ] **Varmepumpe**: Hvilken type/modell? Har den eget styringssystem i dag?
- [ ] **Styring i dag**: Hvordan styres pumpen na — enkel av/pa, eller modulerende effekt?
- [ ] **Rele-behov**: Er det enkel av/pa (230V kontaktor), eller kreves kommunikasjon (Modbus, RS485, etc.)?
- [ ] **Sirkulasjonspumpe**: Egen pumpe i bakkeloyfen, eller drives den av varmepumpen?
- [ ] **Areal**: Hvor stort areal dekker bakkeloyfen?
- [ ] **Treghet**: Hvor lang tid fra oppstart til bakken er varm — minutter eller timer?
- [ ] **Eksisterende sensorer**: Finnes det allerede temperaturfolere i systemet (tur/retur)?

## B. Infrastruktur pa stedet

- [ ] **Strom**: Har RPi tilgang til strom der den skal monteres?
- [ ] **Nettverk**: WiFi eller Ethernet tilgjengelig?
- [ ] **Plassering**: Innendors (teknisk rom) eller utendors (kapsling nodvendig)?

## C. Prediktiv logikk

- [ ] **Treghet i systemet**: Noyaktig tidsforsinkning fra oppstart til effekt (avgjor hvor langt frem vi ma prediktere)
- [ ] **Temperaturgrenser**: Hvilket omrade er "farlig"? (typisk 0 til -5 grader C med fukt)
- [ ] **Prioritet**: Optimalisere for energibruk eller for 100% sikkerhet mot is?

## D. Funksjonelle onsker

- [ ] **Varsling**: Onskes varsling pa mobil (SMS/push) ved oppstart, feil, etc.?
- [ ] **Fjernstyring**: Skal systemet kunne styres fra utenfor lokalt nett?
- [ ] **Logging**: Hvor lenge skal historikk lagres?
- [ ] **Integrasjoner**: Onskes integrasjon med smarthus (Home Assistant, etc.)?
