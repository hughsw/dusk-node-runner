<script lang="ts">
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
</script>

<h1>{data.title}</h1>
<h2>blog/[slug]/</h2>

<div>{@html data.content}</div>
