export async function getHealth(): Promise<{ status: string }> {
  const response = await fetch("/health/live");
  return response.json();
}
