document.getElementById("uploadForm").addEventListener("submit", async function (e) {
  e.preventDefault();

  const formData = new FormData();
  formData.append("file", document.getElementById("file").files[0]);
  formData.append("job_role", document.getElementById("job_role").value);

  const res = await fetch("/upload", {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  if (data.error) {
    alert(data.error);
    return;
  }

  document.getElementById("score").innerText = data.score;
  document.getElementById("matched").innerText = data.found.join(", ");
  document.getElementById("missing").innerText = data.missing.join(", ");

  const aiRes = await fetch("/ai_suggestions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume_text: data.resume_text }),
  });

  const aiData = await aiRes.json();
  document.getElementById("ai_suggestions").innerText = aiData.ai_suggestions;

  // Store for PDF
  window.reportData = {
    matched: data.found,
    missing: data.missing,
    score: data.score,
    suggestions: aiData.ai_suggestions
  };

  document.getElementById("result").style.display = "block";
});

document.getElementById("downloadBtn").addEventListener("click", async function () {
  const response = await fetch("/download_report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(window.reportData),
  });

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "resume_report.pdf";
  a.click();
  window.URL.revokeObjectURL(url);
});
