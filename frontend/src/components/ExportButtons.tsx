import { saveAs } from 'file-saver';
import { jsPDF } from 'jspdf';

type ExportButtonsProps = {
  content: string;
  filename: string;
};

export function ExportButtons({ content, filename }: ExportButtonsProps) {
  const exportAsTxt = () => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    saveAs(blob, `${filename}.txt`);
  };

  const exportAsPdf = () => {
    const doc = new jsPDF();
    doc.text(content, 10, 10);
    doc.save(`${filename}.pdf`);
  };

  return (
    <div className="flex space-x-4 mb-6">
      <button
        onClick={exportAsTxt}
        className="bg-gray-200 dark:bg-gray-700 px-4 py-2 rounded"
      >
        Baixar TXT
      </button>
      <button
        onClick={exportAsPdf}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        Baixar PDF
      </button>
    </div>
  );
}