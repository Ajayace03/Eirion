import { useWizardStore } from "../store/wizardStore";
import Step1Demographics from "../components/wizard/Step1Demographics";
import Step2Genetics from "../components/wizard/Step2Genetics";
import Step3Lifestyle from "../components/wizard/Step3Lifestyle";
import Step4Regimen from "../components/wizard/Step4Regimen";
import Step5Labs from "../components/wizard/Step5Labs";
import Step6Confirm from "../components/wizard/Step6Confirm";

export default function Wizard() {
  const { step, setStep, patient } = useWizardStore();

  const totalSteps = 6;

  const handleNext = () => {
    if (step < totalSteps) setStep(step + 1);
  };

  const handleBack = () => {
    if (step > 1) setStep(step - 1);
  };

  const canProceed = () => {
    if (step === 1) return !!(patient.age && patient.sex && patient.weight_kg);
    return true; // Simple validation for prototype
  };

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
      
      {/* Progress Bar Header */}
      <div className="mb-10 lg:mb-14 px-4 sm:px-0">
        <div className="flex justify-between items-center mb-4">
          <span className="text-sm font-bold text-blue-gray-400 tracking-wider uppercase">Step {step} of {totalSteps}</span>
          <span className="text-sm font-medium text-brand-green bg-brand-green/10 px-3 py-1 rounded-full">
            {Math.round((step / totalSteps) * 100)}% Complete
          </span>
        </div>
        <div className="h-3 w-full bg-blue-gray-100 rounded-full overflow-hidden flex">
          {[...Array(totalSteps)].map((_, i) => (
            <div
              key={i}
              className={`h-full flex-1 transition-all duration-500 ease-out border-r border-white/20 last:border-0 ${
                i < step ? "bg-brand-green shadow-[0_0_10px_rgba(16,185,129,0.5)]" : "bg-transparent"
              }`}
            />
          ))}
        </div>
      </div>

      {/* Main Content Card */}
      <div className="bg-white rounded-[2rem] shadow-xl shadow-blue-gray-200/20 border border-blue-gray-100 p-8 sm:p-12 mb-8 min-h-[500px] flex flex-col">
        <div className="flex-1">
          {step === 1 && <Step1Demographics />}
          {step === 2 && <Step2Genetics />}
          {step === 3 && <Step3Lifestyle />}
          {step === 4 && <Step4Regimen />}
          {step === 5 && <Step5Labs />}
          {step === 6 && <Step6Confirm />}
        </div>

        {/* Navigation Footer */}
        {step < totalSteps && (
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
              Continue
            </button>
          </div>
        )}
      </div>

    </div>
  );
}
