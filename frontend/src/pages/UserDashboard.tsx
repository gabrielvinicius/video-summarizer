import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import api from "../services/api";
import { Video } from "../types";
import { toast } from "react-toastify";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

export default function UserDashboard() {
  const { user, logout } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [videos, setVideos] = useState<Video[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const videosPerPage = 5;
  const navigate = useNavigate();

  // Filtros e paginação
  const filteredVideos = videos.filter((video) => {
    const matchesStatus = statusFilter === "ALL" || video.status === statusFilter;
    const matchesSearch = video.file_name?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && (searchTerm === "" || matchesSearch);
  });

  const paginatedVideos = filteredVideos.slice(
    (currentPage - 1) * videosPerPage,
    currentPage * videosPerPage
  );

  // Upload de vídeo
  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setUploadProgress(0);
    const formData = new FormData();
    formData.append("file", file);

    try {
      await api.post("/videos/upload", formData, {
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 1)
          );
          setUploadProgress(percentCompleted);
        },
      });
      toast.success("Vídeo enviado com sucesso!");
      loadUserVideos();
    } catch (error) {
      toast.error("Falha no upload. Tente novamente.");
    } finally {
      setIsUploading(false);
      setFile(null);
    }
  };

  // Carrega vídeos do usuário
  const loadUserVideos = async () => {
    try {
      const response = await api.get("/videos/me");
      setVideos(response.data);
    } catch (error) {
      toast.error("Falha ao carregar vídeos.");
    }
  };

  // Efeito inicial
  useEffect(() => {
    loadUserVideos();
  }, []);

  // Componente de card de vídeo
  const VideoCard = ({ video }: { video: Video }) => {
    const [showPreview, setShowPreview] = useState(false);

    const downloadVideo = () => {
      window.open(`${import.meta.env.VITE_API_URL}/videos/${video.id}/download`, "_blank");
    };

    return (
      <div className="border rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700 mb-4">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="font-medium">
              {video.file_name || `Vídeo ${video.id.slice(0, 8)}...`}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Status: {video.status} | {new Date(video.created_at).toLocaleString()}
            </p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setShowPreview(!showPreview)}
              className="text-blue-500 hover:underline text-sm"
            >
              {showPreview ? "Ocultar" : "Preview"}
            </button>
            <button
              onClick={downloadVideo}
              className="text-green-500 hover:underline text-sm"
            >
              Baixar
            </button>
          </div>
        </div>

        {showPreview && (
          <div className="mt-4">
            <video controls className="w-full rounded-lg max-h-64">
              <source
                src={`${import.meta.env.VITE_API_URL}/videos/${video.id}/stream`}
                type="video/mp4"
              />
              Seu navegador não suporta vídeos HTML5.
            </video>
          </div>
        )}

        {video.status === "COMPLETED" && (
          <div className="mt-3 flex space-x-3">
            <button
              onClick={() => navigate(`/summaries/${video.id}`)}
              className="text-green-600 hover:underline text-sm"
            >
              Ver Resumo
            </button>
            <button
              onClick={() => navigate(`/transcriptions/${video.id}`)}
              className="text-purple-600 hover:underline text-sm"
            >
              Ver Transcrição
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="p-8 max-w-4xl mx-auto dark:bg-gray-900 min-h-screen">
      <ToastContainer position="bottom-right" autoClose={3000} />
      
      {/* Cabeçalho */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold dark:text-white">Meus Vídeos</h1>
        <button
          onClick={logout}
          className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
        >
          Sair
        </button>
      </div>

      {/* Seção de Upload */}
      <div className="mb-8 p-6 border rounded-lg bg-gray-50 dark:bg-gray-800">
        <h2 className="text-xl font-semibold mb-4 dark:text-white">Enviar Novo Vídeo</h2>
        
        <input
          type="file"
          accept="video/*"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="mb-4 block w-full text-sm text-gray-500
            file:mr-4 file:py-2 file:px-4
            file:rounded file:border-0
            file:text-sm file:font-semibold
            file:bg-blue-50 file:text-blue-700
            hover:file:bg-blue-100
            dark:file:bg-blue-900 dark:file:text-blue-100"
          disabled={isUploading}
        />
        
        {isUploading && (
          <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
            <div
              className="bg-blue-600 h-2.5 rounded-full"
              style={{ width: `${uploadProgress}%` }}
            ></div>
            <p className="text-sm mt-1 dark:text-white">{uploadProgress}%</p>
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={!file || isUploading}
          className={`bg-blue-500 text-white px-4 py-2 rounded ${
            (!file || isUploading) ? "opacity-50 cursor-not-allowed" : "hover:bg-blue-600"
          }`}
        >
          {isUploading ? "Enviando..." : "Enviar Vídeo"}
        </button>
      </div>

      {/* Filtros e Busca */}
      <div className="mb-6 flex flex-col md:flex-row gap-4">
        <input
          type="text"
          placeholder="Buscar vídeos..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="p-2 border rounded flex-grow dark:bg-gray-800 dark:text-white"
        />
        
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="p-2 border rounded dark:bg-gray-800 dark:text-white"
        >
          <option value="ALL">Todos</option>
          <option value="COMPLETED">Completos</option>
          <option value="PROCESSING">Processando</option>
          <option value="FAILED">Falhas</option>
        </select>
      </div>

      {/* Lista de Vídeos */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4 dark:text-white">Histórico</h2>
        
        {paginatedVideos.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400">
            {filteredVideos.length === 0 ? "Nenhum vídeo encontrado." : "Nenhum vídeo nesta página."}
          </p>
        ) : (
          <div className="space-y-4">
            {paginatedVideos.map((video) => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>
        )}
      </div>

      {/* Paginação */}
      {filteredVideos.length > videosPerPage && (
        <div className="flex justify-center mt-6">
          {Array.from({ length: Math.ceil(filteredVideos.length / videosPerPage) }).map((_, i) => (
            <button
              key={i}
              onClick={() => setCurrentPage(i + 1)}
              className={`mx-1 px-3 py-1 rounded ${
                currentPage === i + 1 
                  ? "bg-blue-500 text-white" 
                  : "bg-gray-200 dark:bg-gray-700 dark:text-white"
              }`}
            >
              {i + 1}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}