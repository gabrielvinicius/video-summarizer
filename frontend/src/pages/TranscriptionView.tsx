import { useParams } from 'react-router-dom';
import { ExportButtons } from '../components/ExportButtons';
import api from '../services/api';

export default function TranscriptionView() {
  const { videoId } = useParams();
  const [transcription, setTranscription] = useState('');

  useEffect(() => {
    api.get(`/transcriptions/${videoId}`).then((res) => setTranscription(res.data.text));
  }, [videoId]);

  return (
    <div className="p-8 max-w-4xl mx-auto dark:bg-dark-100 dark:text-white">
      <h1 className="text-2xl font-bold mb-6">Transcrição do Vídeo</h1>
      <ExportButtons content={transcription} filename={`transcricao-${videoId}`} />
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <p className="whitespace-pre-line">{transcription}</p>
      </div>
    </div>
  );
}