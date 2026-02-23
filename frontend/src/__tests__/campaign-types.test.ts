// ============================================================
// TEST UNITARIO: src/types/campaign.ts
// ============================================================
//
// Aquí testeamos las CONSTANTES y FUNCIONES PURAS del dominio.
// Estas son las reglas de negocio del RewardHub:
//   - ¿Qué tipos de campaña existen?
//   - ¿Qué recompensas acepta cada tipo?
//   - ¿El estado inicial de una campaña es correcto?
//
// Por qué testear esto: si alguien cambia por error qué rewards
// acepta "Bet & Get", el test falla y nos avisa antes de
// llegar a producción.
// ============================================================

import { describe, it, expect } from "vitest";
import {
  COUNTRIES,
  CAMPAIGN_TYPES,
  REWARD_TYPES,
  getInitialCampaignData,
} from "@/types/campaign";

// ----- PAÍSES -----------------------------------------------
describe("COUNTRIES — configuración de países disponibles", () => {
  it("tiene exactamente 4 países configurados", () => {
    expect(COUNTRIES).toHaveLength(4);
  });

  it("Nigeria está activa y usa NGN", () => {
    const nigeria = COUNTRIES.find((c) => c.code === "NG");
    expect(nigeria).toBeDefined();
    expect(nigeria?.status).toBe("active");
    expect(nigeria?.currency.code).toBe("NGN");
  });

  it("Kenya está bloqueada (blocked)", () => {
    const kenya = COUNTRIES.find((c) => c.code === "KE");
    expect(kenya?.status).toBe("blocked");
  });

  it("todos los países tienen flag, nombre y moneda", () => {
    for (const country of COUNTRIES) {
      expect(country.flag).toBeTruthy();
      expect(country.name).toBeTruthy();
      expect(country.currency.symbol).toBeTruthy();
    }
  });
});

// ----- TIPOS DE CAMPAÑA -------------------------------------
describe("CAMPAIGN_TYPES — reglas de negocio por tipo de campaña", () => {
  it("existen exactamente 4 tipos de campaña", () => {
    expect(CAMPAIGN_TYPES).toHaveLength(4);
  });

  it("el tipo 'bet-and-get' NO permite bonus-wallet como reward", () => {
    const betAndGet = CAMPAIGN_TYPES.find((c) => c.type === "bet-and-get");
    expect(betAndGet?.allowedRewards).not.toContain("bonus-wallet");
  });

  it("el tipo 'simple' permite los 4 tipos de reward", () => {
    const simple = CAMPAIGN_TYPES.find((c) => c.type === "simple");
    expect(simple?.allowedRewards).toContain("free-bet");
    expect(simple?.allowedRewards).toContain("free-spins");
    expect(simple?.allowedRewards).toContain("cash");
    expect(simple?.allowedRewards).toContain("bonus-wallet");
  });

  it("todos los tipos de campaña tienen título y descripción", () => {
    for (const ct of CAMPAIGN_TYPES) {
      expect(ct.title).toBeTruthy();
      expect(ct.description).toBeTruthy();
    }
  });
});

// ----- REWARD TYPES -----------------------------------------
describe("REWARD_TYPES — catálogo de recompensas", () => {
  it("existen 4 tipos de reward", () => {
    expect(REWARD_TYPES).toHaveLength(4);
  });

  it("el tipo 'free-bet' existe en el catálogo", () => {
    const freeBet = REWARD_TYPES.find((r) => r.type === "free-bet");
    expect(freeBet).toBeDefined();
    expect(freeBet?.title).toBe("Free Bet");
  });
});

// ----- ESTADO INICIAL DE CAMPAÑA ----------------------------
describe("getInitialCampaignData() — estado inicial del wizard", () => {
  it("devuelve country null (el usuario no ha seleccionado ninguno)", () => {
    const data = getInitialCampaignData();
    expect(data.country).toBeNull();
  });

  it("devuelve campaignType null (el usuario no ha elegido tipo)", () => {
    const data = getInitialCampaignData();
    expect(data.campaignType).toBeNull();
  });

  it("la lista de rewards seleccionados empieza vacía", () => {
    const data = getInitialCampaignData();
    expect(data.selectedRewards).toEqual([]);
  });

  it("cada llamada devuelve un objeto NUEVO (no el mismo por referencia)", () => {
    // Importante: si devolviera siempre el mismo objeto, cambiar
    // uno afectaría a todos los wizards abiertos a la vez.
    const a = getInitialCampaignData();
    const b = getInitialCampaignData();
    expect(a).not.toBe(b); // distinta referencia
    expect(a).toEqual(b);  // mismo contenido
  });

  it("la configuración general tiene valores por defecto correctos", () => {
    const { generalConfig } = getInitialCampaignData();
    expect(generalConfig.name).toBe("");
    expect(generalConfig.isPermanent).toBe(false);
    expect(generalConfig.requiresOptIn).toBe(false);
    expect(generalConfig.audienceType).toBe("open");
  });
});
