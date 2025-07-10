<script lang="ts">
	let { children } = $props();
</script>

<nav>
	<a href="/">Duskies</a>
	<a href="/about">About</a>
	<a href="/settings">Settings</a>
	<a href="/sandbox">Sandbox</a>
</nav>

{@render children()}
