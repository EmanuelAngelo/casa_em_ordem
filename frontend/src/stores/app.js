// Utilities
import { defineStore } from "pinia";
import api from "@/api/axios";

export const useAppStore = defineStore("app", {
  state: () => ({
    usuario: null,
    grupoAtual: null,
    moradores: [],
  }),

  actions: {
    async fetchUsuario() {
      try {
        const { data } = await api.get("/users/me/");
        this.usuario = data;
        return data;
      } catch (e) {
        console.error("Erro ao buscar usuário", e);
      }
    },

    async fetchGrupoAtual() {
      try {
        const { data } = await api.get("/grupos/meu/");
        this.grupoAtual = data;
        this.moradores = data.membros || [];
        return data;
      } catch (e) {
        console.error("Erro ao buscar grupo atual", e);
      }
    },

    async fetchMoradores() {
      try {
        const { data } = await api.get("/moradores/");
        this.moradores = data;
        return data;
      } catch (e) {
        console.error("Erro ao buscar moradores", e);
      }
    },
  },
});
