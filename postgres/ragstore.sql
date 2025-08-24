
-- public.docstore definition
-- Drop table
-- DROP TABLE public.docstore;

CREATE TABLE public.docstore (
	id serial4 NOT NULL,
	"key" text NOT NULL,
	value jsonb NULL,
	CONSTRAINT docstore_key_key UNIQUE ("key"),
	CONSTRAINT documents_pkey PRIMARY KEY (id)
);

-- public.file definition
-- Drop table
-- DROP TABLE public.file;

CREATE TABLE public.file (
	id serial4 NOT NULL,
	filename text NOT NULL,
	meta jsonb NOT NULL,
	created_at timestamptz NULL DEFAULT now(),
	created_by int4 NULL,
	CONSTRAINT unique_filename UNIQUE (filename),
	CONSTRAINT uploaded_files_pkey PRIMARY KEY (id)
);

-- public.thread definition
-- Drop table
-- DROP TABLE public.thread;

CREATE TABLE public.thread (
	id serial4 NOT NULL,
	thread_id uuid NOT NULL,
	thread_name varchar NULL DEFAULT ''::character varying,
	user_id int4 NULL,
	created_at timestamptz NULL DEFAULT now(),
	last_modified_at timestamptz NULL DEFAULT now(),
	deleted_at timestamptz NULL,
	CONSTRAINT thread_pkey PRIMARY KEY (id),
	CONSTRAINT thread_thread_id_unique UNIQUE (thread_id)
);

-- public.message definition
-- Drop table
-- DROP TABLE public.message;

CREATE TABLE public.message (
	id serial4 NOT NULL,
	thread_id int4 NOT NULL,
	message_id uuid NOT NULL,
	message text NOT NULL,
	response text NULL,
	intermediate_steps jsonb NULL,
	feedback bool NULL,
	feedback_comment text NULL,
	created_at timestamptz NULL DEFAULT now(),
	last_modified_at timestamptz NULL DEFAULT now(),
	deleted_at timestamptz NULL,
	CONSTRAINT message_message_id_unique UNIQUE (message_id),
	CONSTRAINT message_pkey PRIMARY KEY (id),
	CONSTRAINT message_thread_id_fkey FOREIGN KEY (thread_id) REFERENCES public.thread(id) ON DELETE CASCADE
);