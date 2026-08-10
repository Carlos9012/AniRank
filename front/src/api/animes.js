import apiClient from "./apiClient";

export async function getAnimeByExternalId(externalId) {
  const { data } = await apiClient.get(`/animes/by-external/${externalId}`);
  return data;
}

export async function getAnime(animeId) {
  const { data } = await apiClient.get(`/animes/${animeId}`);
  return data;
}

export async function listAnimes({ skip = 0, limit = 20 } = {}) {
  const { data } = await apiClient.get("/animes/", { params: { skip, limit } });
  return data;
}

export async function searchAnilist(query, limit = 10) {
  const { data } = await apiClient.get("/animes/search", { params: { query, limit } });
  return data;
}

export async function importAnime(externalId) {
  const { data } = await apiClient.post(`/animes/import/${externalId}`);
  return data;
}