const rupee = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" });

export const money = (n) => rupee.format(n);

export function unitWord(form) {
  const f = form || "";
  if (f.includes("capsule")) return "capsules";
  if (f.includes("tablet")) return "tablets";
  return "units";
}
