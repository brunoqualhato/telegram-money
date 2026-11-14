import { Cpu } from "lucide-react";
import Empty from "../../components/ui/Empty.jsx";
import Pagination from "../../components/ui/Pagination.jsx";
import QueueRow from "./QueueRow.jsx";

export default function QueueTable({
  pagedJobs,
  totalItems,
  page,
  pageSize,
  totalPages,
  setPage,
  setPageSize,
  onCancel,
  onRetry,
  onPrioritize,
}) {
  if (totalItems === 0) {
    return <Empty icon={Cpu} text="Nenhuma tarefa na fila de processamento." />;
  }

  return (
    <>
      <div className="table-responsive">
        <table>
          <thead>
            <tr>
              <th style={{ width: "110px" }}>Status</th>
              <th>Tarefa / Processo</th>
              <th style={{ width: "100px" }}>Alvo</th>
              <th style={{ width: "120px" }}>Prioridade</th>
              <th style={{ width: "140px" }}>Criado em</th>
              <th style={{ width: "90px", textAlign: "right" }}>Ações</th>
            </tr>
          </thead>
          <tbody>
            {pagedJobs.map((job) => (
              <QueueRow
                key={job.id}
                job={job}
                onCancel={onCancel}
                onRetry={onRetry}
                onPrioritize={onPrioritize}
              />
            ))}
          </tbody>
        </table>
      </div>
      <Pagination
        page={page}
        pageSize={pageSize}
        totalItems={totalItems}
        totalPages={totalPages}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />
    </>
  );
}
