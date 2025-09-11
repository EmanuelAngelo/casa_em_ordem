<template>
  <v-container fluid>
    <v-row>
      <!-- Coluna Principal: Meu Casal -->
      <v-col cols="12" md="8">
        <v-card>
          <v-toolbar color="blue-darken-3">
            <v-toolbar-title>Meu Casal</v-toolbar-title>
            <v-spacer />
            <v-btn icon @click="loadCasal" :disabled="saving || loading"
              ><v-icon>mdi-refresh</v-icon></v-btn
            >
          </v-toolbar>

          <v-card-text>
            <v-skeleton-loader
              v-if="loading"
              type="article, actions"
            ></v-skeleton-loader>

            <v-row v-else-if="casal">
              <!-- Sub-Coluna Esquerda: Informações e Salários -->
              <v-col cols="12" lg="6">
                <div>
                  <v-text-field
                    v-model="casal.nome"
                    label="Nome do Casal"
                    variant="outlined"
                    density="compact"
                    class="mb-4"
                  />
                  <v-list-subheader>Membros e Salários</v-list-subheader>
                  <div
                    v-for="membro in casal.membros"
                    :key="membro.id"
                    class="mb-3"
                  >
                    <v-text-field
                      v-model.number="membro.salario_mensal"
                      :label="`Salário de ${
                        membro.usuario.first_name || membro.usuario.username
                      }`"
                      type="number"
                      step="0.01"
                      prefix="R$"
                      variant="outlined"
                      density="compact"
                      hide-details
                    />
                  </div>
                  <v-btn
                    color="blue-darken-3"
                    :loading="saving"
                    @click="saveMembros"
                    class="mt-2"
                  >
                    Salvar Alterações
                  </v-btn>
                </div>
              </v-col>

              <!-- Sub-Coluna Direita: Convite (Lógica Original) -->
              <v-col cols="12" lg="6">
                <v-card variant="outlined" class="fill-height">
                  <v-card-title>Adicionar parceiro(a)</v-card-title>
                  <v-card-subtitle
                    >Adicione um usuário já cadastrado.</v-card-subtitle
                  >
                  <v-card-text>
                    <v-form
                      @submit.prevent="onInvite"
                      :disabled="loadingInvite"
                    >
                      <v-text-field
                        v-model="usernameOrEmail"
                        label="Username ou e-mail"
                        prepend-inner-icon="mdi-account-plus"
                        required
                      />
                      <v-btn
                        color="blue-darken-3"
                        :loading="loadingInvite"
                        type="submit"
                      >
                        Adicionar
                      </v-btn>
                      <v-alert
                        v-if="inviteMsg"
                        class="mt-4"
                        :type="inviteType"
                        variant="tonal"
                      >
                        {{ inviteMsg }}
                      </v-alert>
                    </v-form>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <v-alert
              v-else
              type="info"
              variant="tonal"
              class="pa-4 text-center"
            >
              <h3 class="text-h6">Você ainda não faz parte de um casal!</h3>
              <p class="mt-2">
                Para começar, peça para seu parceiro(a) adicionar você (pelo seu
                username ou e-mail) ao casal dele(a).
              </p>
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Coluna de Segurança -->
      <v-col cols="12" md="4">
        <v-card>
          <v-toolbar color="grey-darken-1">
            <v-toolbar-title>Segurança</v-toolbar-title>
          </v-toolbar>
          <v-card-text>
            <v-form @submit.prevent="changePassword" :disabled="savingPassword">
              <v-text-field
                v-model="passwordForm.nova_senha"
                label="Nova Senha"
                type="password"
                prepend-inner-icon="mdi-lock"
                class="mb-2"
                :error-messages="passwordErrors.nova_senha"
                required
              />
              <v-text-field
                v-model="passwordForm.confirmacao_senha"
                label="Confirmar Nova Senha"
                type="password"
                prepend-inner-icon="mdi-lock-check"
                :error-messages="passwordErrors.confirmacao_senha"
                required
              />
              <v-btn
                color="blue-darken-3"
                type="submit"
                :loading="savingPassword"
                class="mt-2"
              >
                Alterar Senha
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import axios from "@/api/axios";

const casal = ref(null);
const loading = ref(true);
const saving = ref(false);
const loadingInvite = ref(false);
const usernameOrEmail = ref(""); // Restaurado
const inviteMsg = ref(""); // Restaurado
const inviteType = ref("info"); // Restaurado
const snackbar = reactive({ show: false, text: "", color: "success" });
const savingPassword = ref(false);
const passwordForm = reactive({ nova_senha: "", confirmacao_senha: "" });
const passwordErrors = ref({});

onMounted(loadCasal);

async function loadCasal() {
  loading.value = true;
  try {
    const { data } = await axios.get("/casais/meu/");
    casal.value = data;
  } catch (e) {
    casal.value = null;
  } finally {
    loading.value = false;
  }
}

async function saveMembros() {
  // ... (função sem alterações)
}

// Função de convite RESTAURADA para a versão original
async function onInvite() {
  inviteMsg.value = "";
  inviteType.value = "info";
  loadingInvite.value = true;
  try {
    const { data } = await axios.post("/casais-extras/convidar/", {
      username_or_email: usernameOrEmail.value.trim(),
    });
    inviteMsg.value = data.detail || "Usuário adicionado ao casal.";
    inviteType.value = "success";
    usernameOrEmail.value = "";
    await loadCasal(); // Recarrega para mostrar o novo membro
  } catch (e) {
    inviteMsg.value =
      e.response?.data?.detail || "Não foi possível adicionar o usuário.";
    inviteType.value = "error";
  } finally {
    loadingInvite.value = false;
  }
}

async function changePassword() {
  // ... (função sem alterações)
}
</script>
