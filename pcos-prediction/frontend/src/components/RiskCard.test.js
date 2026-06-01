import { render, screen } from "@testing-library/react";
import RiskCard from "@/components/RiskCard";

describe("RiskCard", () => {
  it("renders the risk result content", () => {
    render(
      <RiskCard
        result={{
          risk_score: 0.78,
          risk_label: "High",
          risk_color: "#E24B4A",
          recommendation: "Consult a specialist.",
          model_version: "v1.3.0",
          prediction_id: "abc-123"
        }}
      />
    );

    expect(screen.getByText("Prediction Summary")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText(/78%|0.78/)).toBeInTheDocument(); // flexible match
  });
});