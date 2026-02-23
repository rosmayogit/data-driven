// ============================================================
// TEST UNITARIO: src/lib/utils.ts
// ============================================================
//
// ¿Qué es un test unitario?
// Un test unitario comprueba que UNA SOLA función o "unidad"
// de código funciona correctamente de forma aislada.
//
// Estructura básica de un test:
//
//   describe("nombre del grupo")  → agrupa tests relacionados
//   it("descripción legible")     → describe qué debería pasar
//   expect(valor).toBe(esperado)  → la aserción (el "assert")
//
// Si la aserción falla → el test falla → hay un bug.
// Si pasa → confiamos en que esa función funciona como esperamos.
// ============================================================

import { describe, it, expect } from "vitest";
import { cn } from "@/lib/utils";

describe("cn() — combina clases CSS de Tailwind", () => {
  // Test 1: caso más básico posible
  it("devuelve una clase simple sin cambios", () => {
    const resultado = cn("text-red-500");
    expect(resultado).toBe("text-red-500");
  });

  // Test 2: combina múltiples clases
  it("combina varias clases en un string", () => {
    const resultado = cn("text-sm", "font-bold", "text-gray-900");
    expect(resultado).toBe("text-sm font-bold text-gray-900");
  });

  // Test 3: elimina valores falsy (undefined, false, null)
  // Esto es importante en componentes donde clases son condicionales
  it("ignora valores falsy (undefined, false, null)", () => {
    const activo = false;
    const resultado = cn("base-class", activo && "activo", undefined, null);
    expect(resultado).toBe("base-class");
  });

  // Test 4: la lógica clave — Tailwind Merge resuelve conflictos
  // Si tienes "p-2" y "p-4" al mismo tiempo, gana el último
  it("cuando hay clases de Tailwind en conflicto, gana la última", () => {
    const resultado = cn("p-2", "p-4");
    expect(resultado).toBe("p-4");
  });

  // Test 5: clases condicionales (patrón muy común en componentes)
  it("aplica clases condicionalmente según un booleano", () => {
    const esError = true;
    const resultado = cn("text-sm", esError ? "text-red-500" : "text-green-500");
    expect(resultado).toBe("text-sm text-red-500");
  });
});
