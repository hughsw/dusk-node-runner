<script lang="ts">
  import type { PageProps } from './$types';

  const { data }: PageProps = $props();
  const response: string = JSON.stringify(data.item);
</script>

<h1>{data.title}</h1>
<h2>items/[id]/</h2>
<div><span class='tt'>{@html response}</span></div>

<style>
  .tt {
    font-family: monospace, monospace;
    border-radius: 0.5em;
    margin: 0 0 1em 0;
    padding: 0.75em;
    background-color: #ddd;
}
</style>
