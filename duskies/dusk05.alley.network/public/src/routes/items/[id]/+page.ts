import type { PageLoad } from './$types';

export const load: PageLoad = async (foo) => {
//export const load: PageLoad = async ({ fetch, params }) => {
  const { fetch, params, url } = foo;
  const q = url.searchParams.get('q');
  //const search = url.searchParams;
  //return { item: search };
  //return { item: foo };
  //const res = await fetch(`/api/items/${params.id}?q=foon`);
  const res = await fetch(`/api/items/${params.id}?q=${q}`);
  //const res = await fetch(`/api/items/${params.id}`);
  const item = await res.json();

  return { item };
};
