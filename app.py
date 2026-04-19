import streamlit as st
from services.chunking import create_chunk_documents
from services.pdf_parser import save_uploaded_pdf, extract_text_from_pdf
from services.embeddings import embed_chunk_documents, get_embedding_dimension
from services.vectordb import store_embedded_documents, get_collection_count
from services.qa_engine import answer_question
from services.summarizer import generate_paper_summaries
from services.topic_extractor import extract_topics_from_text, get_topic_content
from services.llm_summarizer import generate_summary_sections
from services.paper_search import search_papers
from services.viva_generator import generate_viva_questions
from services.paper_compare import compare_papers
from services.lit_review_generator import generate_lit_review
from services.llm_answer import generate_llm_answer

from dotenv import load_dotenv
load_dotenv()

if "pdf_data" not in st.session_state:
    st.session_state["pdf_data"] = None

if "uploaded_pdf_name" not in st.session_state:
    st.session_state["uploaded_pdf_name"] = None

if "topic_options" not in st.session_state:
    st.session_state["topic_options"] = []

if "topic_summary" not in st.session_state:
    st.session_state["topic_summary"] = None

if "full_paper_summary" not in st.session_state:
    st.session_state["full_paper_summary"] = None

if "summary_mode" not in st.session_state:
    st.session_state["summary_mode"] = None


if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

if "pending_question" not in st.session_state:
    st.session_state["pending_question"] = None

if "current_chat_file" not in st.session_state:
    st.session_state["current_chat_file"] = None

st.set_page_config(page_title="AI Research Paper Assistant", layout="wide")

st.title("AI Research Paper Assistant for Students")

menu = st.sidebar.selectbox(
    "Choose Feature",
    [
        "Search Papers",
        "Upload & Summarize",
        "Ask Questions",
        "Generate Viva Questions",
        "Compare Papers",
        "Generate Literature Review"
    ]
)

if menu == "Search Papers":
    st.subheader("Search Research Papers")

    topic_query = st.text_input(
        "Enter topic",
        placeholder="e.g. LLM, computer vision, breast cancer"
    )
    author_query = st.text_input(
        "Enter author name",
        placeholder="e.g. John Doe"
    )

    if st.button("Search Papers"):
        if topic_query.strip() or author_query.strip():
            try:
                with st.spinner("Searching papers..."):
                    papers = search_papers(
                        topic=topic_query,
                        author_name=author_query,
                        limit=10
                    )

                if papers:
                    st.success(f"Found {len(papers)} paper(s).")

                    for i, paper in enumerate(papers, start=1):
                        st.markdown(f"### {i}. {paper.get('title', 'No title')}")
                        st.write(f"**Authors:** {paper.get('authors', 'N/A')}")
                        st.write(f"**Year:** {paper.get('year', 'N/A')}")
                        st.write(f"**Abstract:** {paper.get('abstract', 'No abstract available')}")
                        if paper.get("url"):
                            st.markdown(f"[Open Paper]({paper['url']})")
                        st.markdown("---")
                else:
                    st.warning("No papers found for the given input.")
            except Exception as e:
                st.error(f"Search failed: {e}")
        else:
            st.warning("Please enter at least a topic or an author name.")

# elif menu == "Upload & Summarize":
#     st.subheader("Upload a Research Paper PDF")

#     uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

#     if uploaded_file:
#         try:
#             # Step 1: Save uploaded PDF
#             pdf_path = save_uploaded_pdf(uploaded_file)

#             # Step 2: Extract text from PDF
#             pdf_data = extract_text_from_pdf(pdf_path)
#             current_file_name = pdf_data["file_name"]

#             if st.session_state.get("current_chat_file") != current_file_name:
#                 st.session_state["chat_history"] = []
#                 st.session_state["current_chat_file"] = current_file_name

#             st.success("PDF uploaded and processed successfully.")
#             st.write(f"**File Name:** {pdf_data['file_name']}")
#             st.write(f"**Pages:** {pdf_data['page_count']}")
#             st.write(f"**Extracted Characters:** {len(pdf_data['clean_text'])}")

#             # Store raw PDF data early
#             st.session_state["pdf_data"] = pdf_data

#             # Optional preview
#             preview_text = pdf_data["clean_text"][:1500]
#             st.text_area("Extracted Text Preview", preview_text, height=250)

#             # Step 3: Create chunks
#             chunk_docs = create_chunk_documents(
#                 text=pdf_data["clean_text"],
#                 source_name=pdf_data["file_name"],
#                 chunk_size=200,
#                 overlap=40
#             )

#             st.write(f"**Total Chunks Created:** {len(chunk_docs)}")

#             if chunk_docs:
#                 st.text_area(
#                     "First Chunk Preview",
#                     chunk_docs[0]["text"],
#                     height=200
#                 )

#             # Step 4: Generate embeddings
#             embedded_docs = embed_chunk_documents(chunk_docs)

#             st.write(f"**Embedding Model Dimension:** {get_embedding_dimension()}")
#             st.write(f"**Embedded Chunks:** {len(embedded_docs)}")

#             if embedded_docs:
#                 st.write(f"**First Embedding Length:** {len(embedded_docs[0]['embedding'])}")

#             # Step 5: Store in ChromaDB
#             stored_count = store_embedded_documents(embedded_docs, reset=True)

#             st.write(f"**Stored in Vector DB:** {stored_count}")
#             st.write(f"**Current Collection Count:** {get_collection_count()}")

#             # Step 6: Store for later
#             st.session_state["chunk_docs"] = chunk_docs
#             st.session_state["embedded_docs"] = embedded_docs

#             st.info("PDF processed successfully. Click the button below to generate summary.")

#             # Step 7: Summarize only when button is clicked
#             if st.button("Summarize Paper"):
#                 with st.spinner("Generating summary..."):
#                     summaries = generate_paper_summaries(pdf_data["clean_text"])

#                 st.session_state["summaries"] = summaries

#                 st.markdown("### Short Summary")
#                 st.write(summaries["short_summary"])

#                 st.markdown("### Detailed Summary")
#                 st.write(summaries["detailed_summary"])

#                 st.markdown("### Beginner-Friendly Summary")
#                 st.write(summaries["beginner_friendly_summary"])

#                 st.markdown("### Methodology Summary")
#                 st.write(summaries["methodology_summary"])

#                 st.markdown("### Results Summary")
#                 st.write(summaries["results_summary"])

#                 st.markdown("### Conclusion Summary")
#                 st.write(summaries["conclusion_summary"])

#         except Exception as e:
#             st.error(f"Error processing PDF: {e}")


elif menu == "Upload & Summarize":
    st.subheader("Upload and Summarize Research Paper")

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    # Process only if a NEW file is uploaded
    if uploaded_file is not None:
        if st.session_state["uploaded_pdf_name"] != uploaded_file.name:
            try:
                pdf_path = save_uploaded_pdf(uploaded_file)
                pdf_data = extract_text_from_pdf(pdf_path)

                st.session_state["pdf_data"] = pdf_data
                st.session_state["uploaded_pdf_name"] = uploaded_file.name

                st.session_state["topic_summary"] = None
                st.session_state["full_paper_summary"] = None
                st.session_state["summary_mode"] = None

                current_file_name = pdf_data["file_name"]
                if st.session_state.get("current_chat_file") != current_file_name:
                    st.session_state["chat_history"] = []
                    st.session_state["current_chat_file"] = current_file_name

                chunk_docs = create_chunk_documents(
                    text=pdf_data["clean_text"],
                    source_name=pdf_data["file_name"],
                    chunk_size=200,
                    overlap=40
                )

                embedded_docs = embed_chunk_documents(chunk_docs)
                store_embedded_documents(embedded_docs, reset=True)

                st.session_state["chunk_docs"] = chunk_docs
                st.session_state["embedded_docs"] = embedded_docs

                topic_options = extract_topics_from_text(pdf_data["raw_text"])
                st.session_state["topic_options"] = topic_options

                st.success(f"Paper '{uploaded_file.name}' uploaded successfully.")

            except Exception as e:
                st.error(f"Error processing PDF: {e}")

    if st.session_state["pdf_data"] is not None:
        pdf_data = st.session_state["pdf_data"]

        st.info(f"Current paper loaded: {pdf_data['file_name']}")

        selected_topic = st.selectbox(
            "Select a topic to summarize",
            st.session_state["topic_options"],
            key="selected_topic_dropdown"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Summarize Topic"):
                try:
                    with st.spinner("Generating topic summary..."):
                        topic_text = get_topic_content(
                            pdf_data["raw_text"],
                            selected_topic
                        )

                        if not topic_text.strip():
                            st.warning(
                                f"Could not extract content specifically for '{selected_topic}'. "
                                f"Try another topic."
                            )
                        else:
                            topic_summary = generate_summary_sections(
                                topic_text,
                                topic_name=selected_topic
                            )

                            st.session_state["topic_summary"] = topic_summary["full_summary"]
                            st.session_state["summary_mode"] = "topic"

                except Exception as e:
                    st.error(f"Error generating topic summary: {e}")

        with col2:
            if st.button("Summarize All"):
                try:
                    with st.spinner("Generating full paper summary..."):
                        full_text = pdf_data["clean_text"][:12000]
                        full_summary = generate_summary_sections(
                            full_text,
                            topic_name="Full Paper"
                        )

                    st.session_state["full_paper_summary"] = full_summary["full_summary"]
                    st.session_state["summary_mode"] = "all"

                except Exception as e:
                    st.error(f"Error generating full paper summary: {e}")

        if st.session_state["summary_mode"] == "topic" and st.session_state["topic_summary"]:
            st.markdown(f"### Summary: {selected_topic}")
            st.write(st.session_state["topic_summary"])

        if st.session_state["summary_mode"] == "all" and st.session_state["full_paper_summary"]:
            st.markdown("### Full Paper Summary")
            st.write(st.session_state["full_paper_summary"])

    else:
        st.warning("Please upload a PDF to begin.")


elif menu == "Ask Questions":
    st.subheader("Chat with Your Research Paper")

    if "pdf_data" not in st.session_state or st.session_state["pdf_data"] is None:
        st.warning("Upload PDF first in Upload & Summarize section.")
    else:
        pdf_name = st.session_state["pdf_data"]["file_name"]

        # Top action buttons
        col1, col2, col3 = st.columns([1, 1, 3])

        with col1:
            if st.button("Clear Chat"):
                st.session_state["chat_history"] = []
                st.rerun()

        with col2:
            if st.button("Clear Suggestions"):
                st.session_state.pop("pending_question", None)
                st.rerun()

        st.markdown("---")

        # Suggested question buttons
        st.markdown("### Try these questions")

        qcol1, qcol2 = st.columns(2)

        with qcol1:
            if st.button("What is this paper about?"):
                st.session_state["pending_question"] = "What is this paper about?"
                st.rerun()

            if st.button("What methodology is used?"):
                st.session_state["pending_question"] = "What methodology is used?"
                st.rerun()

            if st.button("What are the main results?"):
                st.session_state["pending_question"] = "What are the main results?"
                st.rerun()

        with qcol2:
            if st.button("What are the limitations?"):
                st.session_state["pending_question"] = "What are the limitations of this paper?"
                st.rerun()

            if st.button("Summarize this paper simply"):
                st.session_state["pending_question"] = "Summarize this paper in simple words."
                st.rerun()

            if st.button("How many pages does this paper have?"):
                st.session_state["pending_question"] = "How many pages does this paper have?"
                st.rerun()

        st.markdown("---")

        # Show existing chat history
        for message in st.session_state["chat_history"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                if message["role"] == "assistant" and message.get("context"):
                    with st.expander("Show supporting context"):
                        st.text_area(
                            "Context",
                            message["context"],
                            height=220,
                            key=f"context_{id(message)}"
                        )

        # Chat input
        typed_question = st.chat_input("Ask something about the paper...")

        # Use pending suggested question if present, otherwise typed question
        user_question = st.session_state.pop("pending_question", None) or typed_question

        if user_question:
            # Save user message
            st.session_state["chat_history"].append({
                "role": "user",
                "content": user_question
            })

            # Show user message immediately
            with st.chat_message("user"):
                st.markdown(user_question)

            # Generate assistant reply
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        result = answer_question(user_question, top_k=6)
                        assistant_reply = result["answer"]

                        st.markdown(assistant_reply)

                        if result.get("context"):
                            with st.expander("Show supporting context"):
                                st.text_area(
                                    "Context",
                                    result["context"],
                                    height=220,
                                    key=f"live_context_{len(st.session_state['chat_history'])}"
                                )

                        # Save assistant message
                        st.session_state["chat_history"].append({
                            "role": "assistant",
                            "content": assistant_reply,
                            "context": result.get("context", "")
                        })

                    except Exception as e:
                        error_msg = f"Error while answering: {e}"
                        st.error(error_msg)

                        st.session_state["chat_history"].append({
                            "role": "assistant",
                            "content": error_msg,
                            "context": ""
                        })


elif menu == "Generate Viva Questions":

    if st.session_state["pdf_data"] is None:
        st.warning("Upload a paper first.")
    else:

        if st.button("Generate Viva Questions"):

            with st.spinner("Generating questions..."):

                questions = generate_viva_questions(
                    st.session_state["pdf_data"]["clean_text"]
                )

            st.write(questions)


elif menu=="Compare Papers":

    paper1=st.file_uploader(
       "Upload Paper 1",
       type=["pdf"],
       key="paper1"
    )

    paper2=st.file_uploader(
       "Upload Paper 2",
       type=["pdf"],
       key="paper2"
    )

    if paper1 and paper2:

        if st.button("Compare"):

            p1=extract_text_from_pdf(
                save_uploaded_pdf(paper1)
            )

            p2=extract_text_from_pdf(
                save_uploaded_pdf(paper2)
            )

            result=compare_papers(
                p1["clean_text"],
                p2["clean_text"]
            )

            st.write(result)


elif menu=="Generate Literature Review":

    papers=st.file_uploader(
       "Upload multiple papers",
       type=["pdf"],
       accept_multiple_files=True
    )

    if papers:

       if st.button("Generate Review"):

          texts=[]

          for p in papers:

             pdf=extract_text_from_pdf(
                 save_uploaded_pdf(p)
             )

             texts.append(
                 pdf["clean_text"]
             )

          review=generate_lit_review(texts)

          st.write(review)