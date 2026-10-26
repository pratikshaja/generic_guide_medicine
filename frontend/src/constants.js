export const IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];
export const MAX_IMAGE_BYTES = 5 * 1024 * 1024;

export const DEFAULT_DISCLAIMER =
  "Not medical advice. Prices are sample data. Always confirm with your doctor or pharmacist before changing any medicine.";

export const EXAMPLES = [
  {
    label: "Everyday medicines",
    text: "Tab Dolo 650 1 tab TDS x 3 days\nTab Azithral 500 1 tab OD x 3 days\nTab Pan 40 1 tab OD before breakfast x 5 days",
  },
  {
    label: "Thyroid tablet and a misspelt name",
    text: "Thyronorm 50 mcg 1 OD empty stomach\nTab amlokind-5 OD\nCetzin 10 HS prn",
  },
  {
    label: "Fever visit with an injection",
    text: "Dx: viral fever\nRx\nSyp Crocin 5ml TDS x 3d\nInj. Pantop 40 IV OD\nTab Azee 500 mg OD x 3d\nTab Zerodol-P 1 BD after food\nAdvice: plenty of fluids, review after 3 days",
  },
];

// Status codes sent by the backend -> label and colour for the badge
export const STATUS = {
  matched: { label: "Generic found", tone: "found" },
  review: { label: "Please verify", tone: "verify" },
  ask_doctor: { label: "Ask your doctor", tone: "doctor" },
  form_mismatch: { label: "Different form", tone: "neutral" },
  not_found: { label: "Not found", tone: "neutral" },
  no_generic: { label: "No generic listed", tone: "neutral" },
  generic_prescribed: { label: "Already generic", tone: "generic" },
};
