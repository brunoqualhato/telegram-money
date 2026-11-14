import AssetForm from "../features/assets/AssetForm.jsx";
import B3ImportModal from "../features/assets/B3ImportModal.jsx";
import RuleForm from "../features/alerts/RuleForm.jsx";
import DocumentForm from "../features/documents/DocumentForm.jsx";
import EventForm from "../features/events/EventForm.jsx";
import TelegramDialog from "../features/settings/TelegramDialog.jsx";
import ConfirmDialog from "../components/ui/ConfirmDialog.jsx";

const FORMS = {
  asset: AssetForm,
  rule: RuleForm,
  document: DocumentForm,
  event: EventForm,
};

export default function AppDialogs({
  modal,
  setModal,
  done,
  data,
  confirm,
  setConfirm,
}) {
  const Form = FORMS[modal?.type];
  const close = () => setModal(null);
  return (
    <>
      {Form && (
        <Form
          asset={modal.asset}
          assets={data.assets}
          close={close}
          done={done}
        />
      )}
      {modal?.type === "telegram" && (
        <TelegramDialog modal={modal} close={close} />
      )}
      {modal?.type === "import-b3" && (
        <B3ImportModal close={close} done={done} />
      )}
      {confirm && (
        <ConfirmDialog
          title={confirm.title}
          onConfirm={confirm.action}
          onClose={() => setConfirm(null)}
        >
          {confirm.text}
        </ConfirmDialog>
      )}
    </>
  );
}
