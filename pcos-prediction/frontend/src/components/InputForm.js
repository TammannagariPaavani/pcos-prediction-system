import { useEffect, useState } from "react";

const FIELD_SECTIONS = [
  {
    title: "Basic Details",
    fields: [
      { name: "age", label: "Age", type: "number" },
      { name: "weight", label: "Weight (kg)", type: "number" },
      { name: "height", label: "Height (cm)", type: "number" },
      { name: "bmi", label: "BMI", type: "number" },
      { name: "blood_group", label: "Blood Group", type: "text" },

      {
        name: "cycle_regularity",
        label: "Cycle Regularity",
        type: "select",
        options: [
          { label: "Irregular", value: "0" },
          { label: "Regular", value: "1" }
        ]
      },

      { name: "cycle_length", label: "Cycle Length", type: "number" },
      { name: "marriage_years", label: "Marriage Years", type: "number" },

      {
        name: "pregnant",
        label: "Pregnant",
        type: "select",
        options: [
          { label: "No", value: "0" },
          { label: "Yes", value: "1" }
        ]
      },

      { name: "abortions", label: "Abortions", type: "number" }
    ]
  },

  // ✅ ADD THIS (IMPORTANT)
  {
    title: "Symptoms",
    fields: [
      { name: "weight_gain", label: "Weight Gain", type: "select", options: [{ label: "No", value: "0" }, { label: "Yes", value: "1" }] },
      { name: "hair_growth", label: "Hair Growth", type: "select", options: [{ label: "No", value: "0" }, { label: "Yes", value: "1" }] },
      { name: "skin_darkening", label: "Skin Darkening", type: "select", options: [{ label: "No", value: "0" }, { label: "Yes", value: "1" }] },
      { name: "hair_loss", label: "Hair Loss", type: "select", options: [{ label: "No", value: "0" }, { label: "Yes", value: "1" }] },
      { name: "pimples", label: "Pimples", type: "select", options: [{ label: "No", value: "0" }, { label: "Yes", value: "1" }] }
    ]
  },

  {
    title: "Lifestyle",
    fields: [
      { name: "fast_food", label: "Fast Food", type: "select", options: [{ label: "No", value: "0" }, { label: "Yes", value: "1" }] },
      { name: "exercise", label: "Exercise", type: "select", options: [{ label: "No", value: "0" }, { label: "Yes", value: "1" }] }
    ]
  },

  {
    title: "Lab Tests (Optional)",
    fields: [
      { name: "fsh", label: "FSH", type: "number", optional: true },
      { name: "lh", label: "LH", type: "number", optional: true },
      { name: "tsh", label: "TSH", type: "number", optional: true },
      { name: "amh", label: "AMH", type: "number", optional: true },
      { name: "prl", label: "PRL", type: "number", optional: true },
      { name: "vit_d3", label: "Vitamin D3", type: "number", optional: true }
    ]
  }
];

// ✅ DEFAULT VALUES FIX
export function createEmptyPredictionValues() {
  return {
    age: "",
    weight: "",
    height: "",
    bmi: "",
    blood_group: "",
    cycle_regularity: "",
    cycle_length: "",
    marriage_years: "",
    pregnant: "",
    abortions: "",

    // ✅ IMPORTANT DEFAULTS
    weight_gain: "0",
    hair_growth: "0",
    skin_darkening: "0",
    hair_loss: "0",
    pimples: "0",
    fast_food: "0",
    exercise: "0",

    fsh: "",
    lh: "",
    tsh: "",
    amh: "",
    prl: "",
    vit_d3: ""
  };
}

function calculateBmi(weight, height) {
  const w = Number(weight);
  const h = Number(height);
  if (!w || !h) return "";
  const hm = h / 100;
  return (w / (hm * hm)).toFixed(2);
}

export default function InputForm({ onSubmit, loading }) {
  const [values, setValues] = useState(createEmptyPredictionValues());
  const [errors, setErrors] = useState({});
  const [step, setStep] = useState(0);

  useEffect(() => {
    setValues((cur) => ({
      ...cur,
      bmi: calculateBmi(cur.weight, cur.height)
    }));
  }, [values.weight, values.height]);

  const currentSection = FIELD_SECTIONS[step];

  const handleChange = (field, val) => {
    setValues((cur) => ({
      ...cur,
      [field.name]: val
    }));
  };

  const validate = () => {
    const e = {};

    currentSection.fields.forEach((f) => {
      if (f.optional) return;

      if (f.name !== "bmi" && !values[f.name]) {
        e[f.name] = "Required";
      }
    });

    setErrors(e);
    return Object.keys(e).length === 0;
  };

  // ✅ FIXED PAYLOAD
  const normalizePayload = () => {
    const payload = {};

    Object.entries(values).forEach(([key, value]) => {
      if (key === "blood_group") {
        payload[key] = value;
      } else if (value === "" || value === null) {
        payload[key] = null;
      } else if (key === "cycle_length") {
        payload[key] = Number(value) < 20 ? 20 : Number(value);
      } else if (key === "abortions") {
        payload[key] = Number(value) < 0 ? 0 : Number(value);
      } else {
        payload[key] = Number(value);
      }
    });

    return payload;
  };

  return (
    <div className="p-6 bg-white rounded-xl shadow">
      <h2 className="text-xl font-bold mb-4">{currentSection.title}</h2>

      <div className="grid gap-4 md:grid-cols-2">
        {currentSection.fields.map((field) => (
          <div key={field.name}>
            <label className="text-sm">{field.label}</label>

            {field.type === "select" ? (
              <select
                value={values[field.name]}
                onChange={(e) => handleChange(field, e.target.value)}
                className="w-full border p-2 rounded"
              >
                <option value="">Select</option>
                {field.options.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type={field.type}
                value={values[field.name]}
                onChange={(e) => handleChange(field, e.target.value)}
                readOnly={field.name === "bmi"}
                className={`w-full border p-2 rounded ${
                  field.name === "bmi" ? "bg-gray-100" : ""
                }`}
              />
            )}

            {field.optional && (
              <p className="text-xs text-gray-400">Optional</p>
            )}

            {errors[field.name] && (
              <p className="text-red-500 text-xs">{errors[field.name]}</p>
            )}
          </div>
        ))}
      </div>

      <div className="mt-4 flex justify-between">
        <button
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0}
          className="px-4 py-2 border rounded"
        >
          Back
        </button>

        {step < FIELD_SECTIONS.length - 1 ? (
          <button
            onClick={() => {
              if (!validate()) return;
              setStep((s) => s + 1);
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded"
          >
            Next
          </button>
        ) : (
          <button
            onClick={() => {
              if (!validate()) return;
              onSubmit(normalizePayload());
            }}
            disabled={loading}
            className="px-4 py-2 bg-green-600 text-white rounded"
          >
            {loading ? "Submitting..." : "Submit"}
          </button>
        )}
      </div>
    </div>
  );
}