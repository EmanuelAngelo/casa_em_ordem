<template>
  <v-data-table
    :headers="headers"
    :items="rows"
    :loading="loading"
    item-key="id"
    density="comfortable"
    class="elevation-1"
  >
    <template #item.cartao="{ item }">
      <div class="d-flex align-center">
        <v-icon size="18" class="me-1">mdi-credit-card-outline</v-icon>
        <span>{{ item.cartao?.nome || "—" }}</span>
      </div>
    </template>

    <template #item.valor_total="{ item }">
      <span class="font-weight-medium">{{ fmtCurrency(item.valor_total) }}</span>
    </template>

    <template #item.parcelas="{ item }">
      <span>
        {{ item.parcelas_total }}x
        <span v-if="item.parcela_atual"> (atual: {{ item.parcela_atual }})</span>
      </span>
    </template>

    <template #item.primeira_competencia="{ item }">
      {{ fmtMonth(item.primeira_competencia) }}
    </template>

    <template #item.primeiro_vencimento="{ item }">
      {{ fmtDate(item.primeiro_vencimento) }}
    </template>

    <template #item.escopo="{ item }">
      <v-chip
        size="small"
        label
        :color="item.escopo === 'PESS' ? 'purple' : 'blue'"
        variant="tonal"
      >
        {{ item.escopo === 'PESS' ? 'Pessoal' : 'Compartilhada' }}
      </v-chip>
    </template>

    <template #item.pagador="{ item }">
      {{ item.pagador?.first_name || item.pagador?.username || '—' }}
    </template>

    <template #item.dono_pessoal="{ item }">
      <span v-if="item.dono_pessoal">
        {{ item.dono_pessoal.first_name || item.dono_pessoal.username }}
      </span>
      <span v-else>—</span>
    </template>

    <template #item.acoes="{ item }">
      <div class="d-flex justify-end">
        <v-tooltip text="Detalhes / Parcelas">
          <template #activator="{ props }">
            <span v-bind="props">
              <v-btn
                variant="text"
                density="comfortable"
                size="small"
                @click="$emit('view-details', item)"
              >
                <v-icon>mdi-eye-outline</v-icon>
              </v-btn>
            </span>
          </template>
        </v-tooltip>
      </div>
    </template>

    <template #no-data>
      <div class="text-center pa-6">Nenhuma compra no cartão encontrada.</div>
    </template>
  </v-data-table>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  items: { type: [Array, Object], default: () => [] },
  loading: { type: Boolean, default: false },
});
defineEmits(["view-details"]);

const headers = [
  { title: "Cartão", key: "cartao", align: "start" },
  { title: "Descrição", key: "descricao", align: "start" },
  { title: "Valor Total", key: "valor_total", align: "end" },
  { title: "Parcelas", key: "parcelas", align: "center" },
  { title: "1ª Competência", key: "primeira_competencia", align: "start" },
  { title: "1º Vencimento", key: "primeiro_vencimento", align: "start" },
  { title: "Escopo", key: "escopo", align: "start" },
  { title: "Pagador", key: "pagador", align: "start" },
  { title: "Dono (se pessoal)", key: "dono_pessoal", align: "start" },
  { title: "Ações", key: "acoes", align: "end", sortable: false },
];

const rows = computed(() => {
  const list = Array.isArray(props.items)
    ? props.items
    : (props.items?.results ?? []);
  return (list || []).map((i, idx) => ({
    id: i.id ?? idx,
    descricao: i.descricao ?? "",
    valor_total: toNumber(i.valor_total),
    parcelas_total: i.parcelas_total ?? 1,
    parcela_atual: i.parcela_atual ?? null, // se o backend mandar
    primeira_competencia: i.primeira_competencia ?? null,
    primeiro_vencimento: i.primeiro_vencimento ?? null,
    escopo: i.escopo ?? "COMP",
    cartao: i.cartao || null,
    pagador: i.pagador || null,
    dono_pessoal: i.dono_pessoal || null,
    raw: i,
  }));
});

function toNumber(v) {
  if (v === null || v === undefined) return 0;
  const n = typeof v === "string" ? Number(v.replace(",", ".")) : Number(v);
  return isNaN(n) ? 0 : n;
}

function fmtCurrency(v) {
  return toNumber(v).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

function fmtDate(v) {
  if (!v) return "—";
  try {
    const d = typeof v === "string" ? new Date(v) : v;
    return d.toLocaleDateString("pt-BR");
  } catch {
    return v;
  }
}

function fmtMonth(v) {
  if (!v) return "—";
  try {
    const d = typeof v === "string" ? new Date(v) : v;
    return d.toLocaleDateString("pt-BR", { month: "2-digit", year: "numeric" });
  } catch {
    if (typeof v === "string" && /^\d{4}-\d{2}/.test(v)) {
      const [y, m] = v.split("-");
      return `${m}/${y}`;
    }
    return v;
  }
}
</script>
