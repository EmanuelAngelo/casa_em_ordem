<template>
  <v-container fluid>
    <v-card>
      <v-toolbar color="blue-darken-3">
        <v-toolbar-title>Subcategorias</v-toolbar-title>
        <v-spacer />

        <!-- Botão criar subcategoria: habilita se tiver grupo, senão tooltip -->
        <template v-if="!hasGroup">
          <v-tooltip text="Crie um grupo para cadastrar subcategorias">
            <template #activator="{ props }">
              <span v-bind="props">
                <v-btn prepend-icon="mdi-plus" :disabled="true"
                  >Nova Subcategoria</v-btn
                >
              </span>
            </template>
          </v-tooltip>
        </template>
        <template v-else>
          <v-btn prepend-icon="mdi-plus" @click="openCreate"
            >Nova Subcategoria</v-btn
          >
        </template>

        <v-btn icon @click="init" :disabled="loading" class="ms-2">
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
      </v-toolbar>

      <v-card-text>
        <!-- Aviso quando NÃO há grupo -->
        <v-alert
          v-if="!hasGroup && !loading"
          type="info"
          variant="tonal"
          class="mb-4"
        >
          <div class="text-body-1">
            Você ainda não tem um grupo. Ao
            <RouterLink to="/meu-grupo">criar um grupo</RouterLink>, as
            <b>categorias e subcategorias padrão</b> serão criadas
            automaticamente.
          </div>
        </v-alert>

        <!-- Carregando -->
        <v-skeleton-loader
          v-if="loading"
          type="article, list-item@3"
        ></v-skeleton-loader>

        <!-- Conteúdo -->
        <div v-else>
          <SubcategoriasList
            :items="subcategorias"
            :categorias="categoriasOptions"
            :loading="loading"
            @refresh="init"
            @create="openCreate"
            @edit="openEdit"
            @delete="onDelete"
          />
        </div>
      </v-card-text>
    </v-card>

    <v-dialog v-model="formDialog" max-width="600px" persistent>
      <SubcategoriasForm
        :model="editedItem"
        :categorias="categoriasOptions"
        :saving="saving"
        @close="formDialog = false"
        @save="onSave"
      />
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="4000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "@/api/axios";
import SubcategoriasList from "@/components/SubcategoriasList.vue";
import SubcategoriasForm from "@/components/SubcategoriasForm.vue";

const loading = ref(false);
const saving = ref(false);
const hasGroup = ref(false);

const subcategorias = ref([]);
const categoriasOptions = ref([]);

const formDialog = ref(false);
const editedItem = ref(null);

const snackbar = ref({ show: false, text: "", color: "success" });

onMounted(init);

async function init() {
  loading.value = true;
  try {
    const { data: grupo } = await axios.get("/grupos/meu/");
    hasGroup.value = !!grupo;

    const { data: cats } = await axios.get("/categorias/");
    const categorias = cats?.results ?? cats ?? [];
    categoriasOptions.value = categorias.map((c) => ({
      label: c.nome,
      value: c.id,
    }));

    const { data: subs } = await axios.get("/subcategorias/");
    subcategorias.value = subs?.results ?? subs ?? [];
  } catch (e) {
    subcategorias.value = [];
    categoriasOptions.value = [];
    console.error("Falha ao carregar subcategorias:", e);
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  if (!hasGroup.value) {
    snackbar.value = {
      show: true,
      text: "Para cadastrar subcategorias, crie um grupo primeiro.",
      color: "info",
    };
    return;
  }
  editedItem.value = { id: null, categoria: null, nome: "", ativa: true };
  formDialog.value = true;
}

function openEdit(item) {
  editedItem.value = {
    ...item,
    categoria: item.categoria?.id || item.categoria,
  };
  formDialog.value = true;
}

async function onSave(payload) {
  saving.value = true;
  try {
    const url = payload.id
      ? `/subcategorias/${payload.id}/`
      : "/subcategorias/";
    const method = payload.id ? "patch" : "post";
    await axios[method](url, payload);
    formDialog.value = false;
    await init();
    snackbar.value = {
      show: true,
      text: "Subcategoria salva com sucesso.",
      color: "success",
    };
  } catch (e) {
    console.error("Erro ao salvar subcategoria:", e);
    snackbar.value = {
      show: true,
      text:
        e.response?.data?.detail ||
        "Não foi possível salvar. Em modo sem grupo, crie um grupo para cadastrar subcategorias.",
      color: "error",
    };
  } finally {
    saving.value = false;
  }
}

async function onDelete(item) {
  try {
    await axios.delete(`/subcategorias/${item.id}/`);
    await init();
    snackbar.value = {
      show: true,
      text: "Subcategoria removida.",
      color: "success",
    };
  } catch (e) {
    console.error("Erro ao remover subcategoria:", e);
    snackbar.value = {
      show: true,
      text:
        e.response?.data?.detail || "Não foi possível remover a subcategoria.",
      color: "error",
    };
  }
}
</script>
