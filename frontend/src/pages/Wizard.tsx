import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useWizardStore } from "../store/wizardStore";
import Step1Demographics from "../components/wizard/Step1Demographics";
import Step2Conditions from "../components/wizard/Step2Conditions";
import Step3GeneticUpload from "../components/wizard/Step3GeneticUpload";
import Step4GeneticManual from "../components/wizard/Step4GeneticManual";
import Step5LabUpload from "../components/wizard/Step5LabUpload";
import Step6Lifestyle from "../components/wizard/Step6Lifestyle";
import Step7Diet from "../components/wizard/Step3Diet";
import Step8Regimen from "../components/wizard/Step8Regimen";
import Step9Confirm from "../components/wizard/Step6Confirm";

const STEP_LABELS = [
  "Demographics",
  "Conditions",
  "Genetics — Upload",
  "Genetics — Manual",
  "Lab Report",
  "Lifestyle",
  "Diet",
  "Regimen",
  "Confirm",
];

const TOTAL_STEPS = 9;

export default function Wizard() {
  const navigate = useNavigate();
  const { step, setStep, patient, regimen, analysisResult } = useWizardStore();

  // If an analysis already exists, don't show the wizard again — go to dashboard
  useEffect(() => {
    if (analysisResult) {
      navigate("/dashboard", { replace: true });
    }
  }, [analysisResult, navigate]);

  const handleNext = () => { if (step < TOTAL_STEPS) setStep(step + 1); };
  const handleBack = () => { if (step > 1) setStep(step - 1); };

  const canProceed = () => {
    if (step === 1) return !!(patient.age && patient.sex && patient.weight_kg);
    if (step === 8) return regimen.length > 0;
    return true; // conditions, genetics, labs are optional
  };

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">

      {/* Progress Bar */}
      <div className="mb-10 lg:mb-14 px-4 sm:px-0">
        <div className="flex justify-between items-center mb-4">
          <span className="text-sm font-bold text-blue-gray-400 tracking-wider uppercase">
            {STEP_LABELS[step - 1]} — Step {step} of {TOTAL_STEPS}
          </span>
          <span className="text-sm font-medium text-brand-green bg-brand-green/10 px-3 py-1 rounded-full">
            {Math.round((step / TOTAL_STEPS) * 100)}% Complete
          </span>
        </div>
        <div className="h-3 w-full bg-blue-gray-100 rounded-full overflow-hidden flex">
          {[...Array(TOTAL_STEPS)].map((_, i) => (
            <div
              key={i}
              className={`h-full flex-1 transition-all duration-500 ease-out border-r border-white/20 last:border-0 ${
                i < step ? "bg-brand-green shadow-[0_0_10px_rgba(16,185,129,0.5)]" : "bg-transparent"
              }`}
            />
          ))}
        </div>
      </div>

      {/* Step Dots */}
      <div className="flex justify-center gap-1.5 mb-8">
        {STEP_LABELS.map((label, i) => (
          <button
            key={i}
            onClick={() => i + 1 < step && setStep(i + 1)}
            title={label}
            className={`transition-all duration-300 rounded-full ${
              i + 1 === step
                ? "w-8 h-2.5 bg-brand-green"
                : i + 1 < step
                ? "w-2.5 h-2.5 bg-brand-green/40 cursor-pointer hover:bg-brand-green/60"
                : "w-2.5 h-2.5 bg-blue-gray-200 cursor-default"
            }`}
          />
        ))}
      </div>

      {/* Main Content Card */}
      <div className="bg-white rounded-[2rem] shadow-xl shadow-blue-gray-200/20 border border-blue-gray-100 p-8 sm:p-12 mb-8 min-h-[500px] flex flex-col">
        <div className="flex-1">
          {step === 1 && <Step1Demographics />}
          {step === 2 && <Step2Conditions />}
          {step === 3 && <Step3GeneticUpload />}
          {step === 4 && <Step4GeneticManual />}
          {step === 5 && <Step5LabUpload />}
          {step === 6 && <Step6Lifestyle />}
          {step === 7 && <Step7Diet />}
          {step === 8 && <Step8Regimen />}
          {step === 9 && <Step9Confirm />}
        </div>

        {/* Skip labels for optional steps */}
        {[2, 3, 4, 5].includes(step) && (
          <p className="text-center text-xs text-blue-gray-400 pt-4 mt-4 border-t border-blue-gray-50">
            This step is optional — click <strong>Continue</strong> to skip.
          </p>
        )}

        {/* Navigation Footer */}
        {step < TOTAL_STEPS && (
          <div className="flex items-center justify-between pt-8 mt-8 border-t border-blue-gray-100">
            <button
              onClick={handleBack}
              disabled={step === 1}
              className="px-6 py-3 font-semibold text-blue-gray-500 hover:text-blue-gray-900 hover:bg-blue-gray-50 rounded-xl transition-all disabled:opacity-0"
            >
              Back
            </button>
            <button
              onClick={handleNext}
              disabled={!canProceed()}
              className="px-8 py-3 bg-blue-gray-900 text-white rounded-xl font-bold shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:hover:translate-y-0"
            >
              Continue →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
