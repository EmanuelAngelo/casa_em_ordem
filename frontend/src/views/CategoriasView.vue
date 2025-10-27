<template>
  <v-container fluid>
    <v-card>
      <v-toolbar color="blue-darken-3">
        <v-toolbar-title>Categorias</v-toolbar-title>
        <v-spacer />

        <!-- Nova Categoria -->
        <template v-if="!hasGroup">
          <v-tooltip text="Crie um grupo para cadastrar categorias">
            <template #activator="{ props }">
              <span v-bind="props">
                <v-btn prepend-icon="mdi-plus" :disabled="true">Nova Categoria</v-btn>
              </span>
            </template>
          </v-tooltip>
        </template>
        <template v-else>
          <v-btn prepend-icon="mdi-plus" @click="openCreateCategoria">Nova Categoria</v-btn>
        </template>

        <!-- Nova Subcategoria -->
        <template v-if="!hasGroup">
          <v-tooltip text="Crie um grupo para cadastrar subcategorias">
            <template #activator="{ props }">
              <span v-bind="props">
                <v-btn prepend-icon="mdi-shape-square-plus" class="ms-2" :disabled="true">
                  Nova Subcategoria
                </v-btn>
              </span>
            </template>
          </v-tooltip>
        </template>
        <template v-else>
          <v-btn prepend-icon="mdi-shape-square-plus" class="ms-2" @click="openCreateSubcategoria">
            Nova Subcategoria
          </v-btn>
        </template>

        <!-- Refresh -->
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
            Você ainda não tem um grupo. Ao <RouterLink to="/meu-grupo">criar um grupo</RouterLink>,
            as <b>categorias e subcategororias padrão</b> serão criadas automaticamente para você começar.
          </div>
        </v-alert>

        <!-- Carregando -->
        <v-skeleton-loader v-if="loading" type="article, list-item@3" />

        <!-- Lista -->
        <div v-else>
          <!-- Passamos a lista como vem da API; o componente normaliza -->
          <CategoriasList
            :items="categorias"
            :loading="loading"
            @refresh="init"
            @create="openCreateCategoria"
            @edit="openEditCategoria"
            @delete="deleteCategoria"
          />
        </div>
      </v-card-text>
    </v-card>

    <!-- Dialog: Nova/Editar Categoria -->
    <v-dialog v-model="categoriaDialog" max-width="520px" persistent>
      <CategoriasForm
        :model="categoriaEdit"
        :saving="saving"
        @close="categoriaDialog = false"
        @save="saveCategoria"
      />
    </v-dialog>

    <!-- Dialog: Nova/Editar Subcategoria -->
    <v-dialog v-model="subcategoriaDialog" max-width="600px" persistent>
      <SubcategoriasForm
        :model="subcategoriaEdit"
        :categorias="categorias"
        :saving="savingSub"
        @close="subcategoriaDialog = false"
        @save="saveSubcategoria"
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
import CategoriasList from "@/components/CategoriasList.vue";
import CategoriasForm from "@/components/CategoriasForm.vue";
import SubcategoriasForm from "@/components/SubcategoriasForm.vue";

const loading = ref(false);
const hasGroup = ref(false);

const categorias = ref([]);

// Categoria dialog
const categoriaDialog = ref(false);
const saving = ref(false);
const categoriaEdit = ref(null);

// Subcategoria dialog
const subcategoriaDialog = ref(false);
const savingSub = ref(false);
const subcategoriaEdit = ref(null);

const snackbar = ref({ show: false, text: "", color: "success" });

onMounted(init);

async function init() {
  loading.value = true;
  try {
    // 1) checa grupo atual
    const { data: grupo } = await axios.get("/grupos/meu/");
    hasGroup.value = !!grupo;

    // 2) carrega categorias (shape da API)
    const { data } = await axios.get("/categorias/");
    categorias.value = data?.results ?? data ?? [];
  } catch (e) {
    categorias.value = [];
    console.error("Falha ao carregar categorias:", e);
  } finally {
    loading.value = false;
  }
}

/* ======== Categoria ======== */
function openCreateCategoria() {
  if (!hasGroup.value) {
    snackbar.value = {
      show: true,
      text: "Para cadastrar categorias, crie um grupo primeiro.",
      color: "info",
    };
    return;
  }
  categoriaEdit.value = { id: null, nome: "", ativa: true };
  categoriaDialog.value = true;
}

function openEditCategoria(item) {
  // item vem normalizado pela lista
  categoriaEdit.value = { ...item };
  categoriaDialog.value = true;
}

async function saveCategoria(payload) {
  saving.value = true;
  try {
    const url = payload.id ? `/categorias/${payload.id}/` : "/categorias/";
    const method = payload.id ? "patch" : "post";
    await axios[method](url, payload);
    categoriaDialog.value = false;
    await init();
    snackbar.value = {
      show: true,
      text: "Categoria salva com sucesso.",
      color: "success",
    };
  } catch (e) {
    console.error("Erro ao salvar categoria:", e);
    snackbar.value = {
      show: true,
      text:
        e.response?.data?.detail ||
        "Não foi possível salvar a categoria. Se você estiver sem grupo, crie um grupo para poder cadastrar.",
      color: "error",
    };
  } finally {
    saving.value = false;
  }
}

async function deleteCategoria(item) {
  try {
    await axios.delete(`/categorias/${item.id}/`);
    await init();
    snackbar.value = { show: true, text: "Categoria removida.", color: "success" };
  } catch (e) {
    console.error("Erro ao remover categoria:", e);
    snackbar.value = {
      show: true,
      text: e.response?.data?.detail || "Não foi possível remover a categoria.",
      color: "error",
    };
  }
}

/* ======== Subcategoria ======== */
function openCreateSubcategoria() {
  if (!hasGroup.value) {
    snackbar.value = {
      show: true,
      text: "Para cadastrar subcategorias, crie um grupo primeiro.",
      color: "info",
    };
    return;
  }
  subcategoriaEdit.value = { id: null, categoria: null, nome: "", ativa: true };
  subcategoriaDialog.value = true;
}

async function saveSubcategoria(payload) {
  savingSub.value = true;
  try {
    const url = payload.id ? `/subcategorias/${payload.id}/` : "/subcategorias/";
    const method = payload.id ? "patch" : "post";
    await axios[method](url, payload);
    subcategoriaDialog.value = false;
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
    savingSub.value = false;
  }
}
</script>
