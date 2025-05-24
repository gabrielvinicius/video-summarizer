import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import api from "../services/api";
import { Video, User } from "../types"; // Tipos definidos abaixo

export default function AdminDashboard() {
  const { logout } = useAuth();
  const [activeTab, setActiveTab] = useState("stats");
  const [videos, setVideos] = useState<Video[]>([]);
  const [users, setUsers] = useState<User[]>([]);

  // Fetch dados ao carregar (exemplo)
  const loadVideos = async () => {
    const response = await api.get("/videos");
    setVideos(response.data);
  };

  const loadUsers = async () => {
    const response = await api.get("/auth/users");
    setUsers(response.data);
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">Painel Administrativo</h1>
        <button
          onClick={logout}
          className="bg-red-500 text-white px-4 py-2 rounded"
        >
          Sair
        </button>
      </div>

      {/* Abas */}
      <div className="flex border-b mb-6">
        <button
          className={`px-4 py-2 ${activeTab === "stats" ? "border-b-2 border-blue-500" : ""}`}
          onClick={() => setActiveTab("stats")}
        >
          Estatísticas
        </button>
        <button
          className={`px-4 py-2 ${activeTab === "videos" ? "border-b-2 border-blue-500" : ""}`}
          onClick={() => { setActiveTab("videos"); loadVideos(); }}
        >
          Vídeos
        </button>
        <button
          className={`px-4 py-2 ${activeTab === "users" ? "border-b-2 border-blue-500" : ""}`}
          onClick={() => { setActiveTab("users"); loadUsers(); }}
        >
          Usuários
        </button>
      </div>

      {/* Conteúdo das Abas */}
      {activeTab === "stats" && <StatsTab />}
      {activeTab === "videos" && <VideoTab videos={videos} />}
      {activeTab === "users" && <UserTab users={users} />}
    </div>
  );
}

// Componentes das Abas
const StatsTab = () => (
  <div>
    <h3 className="text-xl mb-4">Métricas do Sistema</h3>
    <div className="grid grid-cols-3 gap-4">
      <MetricCard title="Vídeos Processados" value="1,234" />
      <MetricCard title="Usuários Ativos" value="56" />
      <MetricCard title="Tempo Médio de Processamento" value="2.5min" />
    </div>
  </div>
);

const VideoTab = ({ videos }: { videos: Video[] }) => (
  <div>
    <h3 className="text-xl mb-4">Últimos Vídeos</h3>
    <table className="w-full border-collapse">
      <thead>
        <tr className="bg-gray-100">
          <th className="p-2 border">ID</th>
          <th className="p-2 border">Status</th>
          <th className="p-2 border">Data</th>
        </tr>
      </thead>
      <tbody>
        {videos.map((video) => (
          <tr key={video.id} className="border">
            <td className="p-2 border">{video.id.slice(0, 8)}...</td>
            <td className="p-2 border">
              <span className={`px-2 py-1 rounded ${
                video.status === "COMPLETED" ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"
              }`}>
                {video.status}
              </span>
            </td>
            <td className="p-2 border">{new Date(video.created_at).toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

const UserTab = ({ users }: { users: User[] }) => (
  <div>
    <h3 className="text-xl mb-4">Usuários Registrados</h3>
    <table className="w-full border-collapse">
      <thead>
        <tr className="bg-gray-100">
          <th className="p-2 border">Email</th>
          <th className="p-2 border">Data de Registro</th>
        </tr>
      </thead>
      <tbody>
        {users.map((user) => (
          <tr key={user.id} className="border">
            <td className="p-2 border">{user.email}</td>
            <td className="p-2 border">{new Date(user.created_at).toLocaleDateString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

// Componente auxiliar
const MetricCard = ({ title, value }: { title: string; value: string }) => (
  <div className="bg-white p-4 rounded shadow">
    <h4 className="text-gray-500 text-sm">{title}</h4>
    <p className="text-2xl font-bold">{value}</p>
  </div>
);