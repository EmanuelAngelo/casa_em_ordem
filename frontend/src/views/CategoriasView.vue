<template>
  <v-container fluid>
    <v-card>
      <v-toolbar color="blue-darken-3">
        <v-toolbar-title>Categorias</v-toolbar-title>
        <v-spacer />
        <v-btn icon @click="fetchCategorias"
          ><v-icon>mdi-refresh</v-icon></v-btn
        >
        <v-btn prepend-icon="mdi-plus" @click="openForm()"
          >Adicionar Categoria</v-btn
        >

        <!-- AJUSTADO: abre o dialog de subcategoria -->
        <v-btn prepend-icon="mdi-shape-outline" @click="openSubForm()">
          Adicionar Subcategoria
        </v-btn>
      </v-toolbar>

      <v-card-text>
        <CategoriasList
          :items="categorias"
          :loading="loading"
          @edit="openForm"
          @delete="confirmDelete"
        />
      </v-card-text>
    </v-card>

    <!-- Dialog Categoria -->
    <v-dialog v-model="dialog" persistent max-width="520px">
      <CategoriasForm
        :model="editedCategoria"
        :saving="saving"
        @close="dialog = false"
        @save="saveCategoria"
      />
    </v-dialog>

    <!-- Dialog Subcategoria -->
    <v-dialog v-model="subDialog" persistent max-width="560px">
      <SubcategoriasForm
        :model="subEdited"
        :categorias="categorias"
        :saving="subSaving"
        :locked-categoria="lockSubCategoria"
        @close="subDialog = false"
        @save="saveSubcategoria"
      />
    </v-dialog>

    <!-- Dialog Confirmar Exclusão -->
    <v-dialog v-model="deleteDialog" persistent max-width="400px">
      <v-card>
        <v-card-title class="text-h5">Confirmar Exclusão</v-card-title>
        <v-card-text
          >Tem certeza que deseja excluir esta categoria?</v-card-text
        >
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="deleteDialog = false">Cancelar</v-btn>
          <v-btn color="red-darken-1" @click="deleteCategoriaConfirmed"
            >Excluir</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog de Erro -->
    <v-dialog v-model="errorDialog" persistent max-width="500px">
      <v-card>
        <v-card-title class="text-h5 bg-red-darken-2">
          <v-icon start icon="mdi-alert-circle-outline" />
          Operação Bloqueada
        </v-card-title>
        <v-card-text class="py-4 text-body-1">{{ errorMessage }}</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            color="blue-darken-1"
            variant="elevated"
            @click="errorDialog = false"
            >Entendi</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "@/api/axios";
import CategoriasList from "@/components/CategoriasList.vue";
import CategoriasForm from "@/components/CategoriasForm.vue";
import SubcategoriasForm from "@/components/SubcategoriasForm.vue";

const categorias = ref([]);
const loading = ref(false);
const saving = ref(false);
const dialog = ref(false);
const deleteDialog = ref(false);

const editedCategoria = ref({});
const categoriaToDelete = ref(null);

const errorDialog = ref(false);
const errorMessage = ref("");

// ---- Subcategoria controls ----
const subDialog = ref(false);
const subEdited = ref({ id: null, nome: "", categoria_id: null, ativa: true });
const subSaving = ref(false);
const lockSubCategoria = ref(false); // AJUSTE: controla se o select da categoria fica travado

onMounted(fetchCategorias);

async function fetchCategorias() {
  loading.value = true;
  try {
    const resp = await axios.get("/categorias/");
    categorias.value = resp.data?.results ?? resp.data ?? [];
  } catch (e) {
    errorMessage.value = "Não foi possível carregar as categorias.";
    errorDialog.value = true;
  } finally {
    loading.value = false;
  }
}

function openForm(item = null) {
  editedCategoria.value = item
    ? { id: item.id, nome: item.nome, ativa: !!item.ativa }
    : { id: null, nome: "", ativa: true };
  dialog.value = true;
}

async function saveCategoria(payload) {
  saving.value = true;
  try {
    const body = {
      id: payload.id ?? undefined,
      nome: payload.nome,
      ativa: !!payload.ativa,
    };
    if (body.id) {
      await axios.patch(`/categorias/${body.id}/`, body);
      dialog.value = false;
      await fetchCategorias();
    } else {
      const { data: created } = await axios.post("/categorias/", body);
      dialog.value = false;
      await fetchCategorias();

      // opcional: já abrir subcategoria com a categoria criada travada
      openSubForm(created.id); // <-- se não quiser abrir automático, remova esta linha
    }
  } catch (e) {
    errorMessage.value = "Não foi possível salvar a categoria.";
    errorDialog.value = true;
  } finally {
    saving.value = false;
  }
}

function confirmDelete(item) {
  categoriaToDelete.value = item;
  deleteDialog.value = true;
}

async function deleteCategoriaConfirmed() {
  try {
    await axios.delete(`/categorias/${categoriaToDelete.value.id}/`);
    deleteDialog.value = false;
    await fetchCategorias();
  } catch (e) {
    deleteDialog.value = false;
    errorMessage.value =
      e.response?.data?.detail || "Erro ao excluir a categoria.";
    errorDialog.value = true;
  }
}

// ------- SUBCATEGORIA -------

// ABRIR o dialog corretamente (com ou sem categoria travada)
function openSubForm(categoriaId = null) {
  lockSubCategoria.value = !!categoriaId; // trava se veio categoria
  subEdited.value = {
    id: null,
    nome: "",
    categoria_id: categoriaId, // quando nulo, usuário escolhe no select
    ativa: true,
  };
  subDialog.value = true;
}

async function saveSubcategoria(payload) {
  subSaving.value = true;
  try {
    const body = { ...payload };
    if (body.id) {
      await axios.patch(`/subcategorias/${body.id}/`, body);
    } else {
      await axios.post("/subcategorias/", body);
    }
    // mantém o dialog para cadastrar várias em sequência
    subEdited.value = {
      id: null,
      nome: "",
      categoria_id: body.categoria_id, // mantém a mesma categoria
      ativa: true,
    };
  } catch (e) {
    errorMessage.value = "Não foi possível salvar a subcategoria.";
    errorDialog.value = true;
  } finally {
    subSaving.value = false;
  }
}
</script>
