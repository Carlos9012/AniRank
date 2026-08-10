import apiClient  from "./apiClient";

export async function register({ email, username, password }) {
  const { data } = await apiClient.post("/auth/register", {
    email,
    username,
    password,
  });
  return data;
}

export async function login({ username, password }) {
  const body = new URLSearchParams();
  body.set("username", username);
  body.set("password", password);

  const { data } = await apiClient.post("/auth/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

export async function getMe() {
  const { data } = await apiClient.get("/auth/me");
  return data;
}
