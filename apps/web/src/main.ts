const root = document.getElementById("root");

if (root) {
  root.innerHTML = `
    <main style="font-family: Georgia, serif; padding: 2rem; max-width: 720px; margin: 0 auto;">
      <h1 style="margin-bottom: 0.5rem;">Procura</h1>
      <p style="margin-top: 0; line-height: 1.6;">
        Dashboard scaffold for active orders, approvals, supplier comparisons, and live workflow status.
      </p>
      <section>
        <h2 style="font-size: 1.1rem;">Planned views</h2>
        <ul>
          <li>Active orders dashboard</li>
          <li>Order detail timeline</li>
          <li>Approvals inbox</li>
          <li>Supplier comparison table</li>
        </ul>
      </section>
    </main>
  `;
}