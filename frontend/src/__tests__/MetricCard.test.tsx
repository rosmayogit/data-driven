// ============================================================
// TEST DE COMPONENTE: MetricCard
// ============================================================
//
// Además de testear funciones puras, podemos testear
// componentes React — comprobamos que renderizan correctamente.
//
// Herramienta: @testing-library/react
// Filosofía: testear lo que VE el usuario, no los internos.
//   ✅ "¿aparece el texto '1,234' en pantalla?"
//   ❌ "¿el estado interno tiene valor 1234?"
//
// render()      → monta el componente en un DOM virtual
// screen        → interfaz para buscar elementos en el DOM
// getByText()   → busca un elemento por su texto (falla si no existe)
// queryByText() → busca un elemento por texto (devuelve null si no existe)
// ============================================================

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MetricCard } from "@/components/MetricCard";
import { Users } from "lucide-react";

describe("MetricCard — tarjeta de métricas del dashboard", () => {
  // Test 1: renderizado básico — ¿aparece el título y el valor?
  it("muestra el título y el valor numérico", () => {
    render(
      <MetricCard
        title="Total Usuarios"
        value="1,234"
        icon={Users}
      />
    );

    // getByText lanza error si no encuentra el texto → test falla
    expect(screen.getByText("Total Usuarios")).toBeInTheDocument();
    expect(screen.getByText("1,234")).toBeInTheDocument();
  });

  // Test 2: la descripción es OPCIONAL — si no se pasa, no aparece
  it("no muestra descripción si no se pasa la prop", () => {
    render(
      <MetricCard
        title="Campañas activas"
        value={42}
        icon={Users}
      />
    );

    // queryByText devuelve null si no existe (no lanza error)
    expect(screen.queryByText(/descripción/i)).toBeNull();
  });

  // Test 3: cuando se pasa descripción, SÍ aparece
  it("muestra la descripción cuando se pasa como prop", () => {
    render(
      <MetricCard
        title="ARPU"
        value="€24.50"
        icon={Users}
        description="Promedio últimos 30 días"
      />
    );

    expect(screen.getByText("Promedio últimos 30 días")).toBeInTheDocument();
  });

  // Test 4: el cambio positivo muestra "+" antes del valor
  it("muestra el prefijo '+' cuando el cambio es positivo", () => {
    render(
      <MetricCard
        title="Conversión"
        value="68%"
        icon={Users}
        change={{ value: "5%", positive: true }}
      />
    );

    // El componente añade "+" delante si positive=true
    expect(screen.getByText(/\+5%/)).toBeInTheDocument();
  });

  // Test 5: el cambio negativo NO muestra "+"
  it("NO muestra '+' cuando el cambio es negativo", () => {
    render(
      <MetricCard
        title="Retención"
        value="32%"
        icon={Users}
        change={{ value: "3%", positive: false }}
      />
    );

    // Buscamos el texto de cambio — no debería tener "+"
    expect(screen.queryByText(/\+3%/)).toBeNull();
    expect(screen.getByText(/3% from last period/)).toBeInTheDocument();
  });
});
