/*ficheiro com o codigo sql para a criação das tabelas
	codigo sql proveniente do ONDA */

CREATE TABLE leilao (
	numero		 SERIAL,
	ean_artigo		 BIGINT NOT NULL,
	preco_minimo	 FLOAT(8) NOT NULL,
	preco_vencedor	 FLOAT(8) DEFAULT 0,
	momento_fim	 TIMESTAMP NOT NULL,
	ativo		 BOOL DEFAULT TRUE,
	titulo		 VARCHAR(512) NOT NULL,
	descricao		 VARCHAR(512) NOT NULL,
	utilizador_username VARCHAR(512) NOT NULL,
	PRIMARY KEY(numero)
);

CREATE TABLE licitacao (
	valor		 BIGINT,
	momento		 TIMESTAMP,
	utilizador_username VARCHAR(512),
	leilao_numero	 INTEGER,
	PRIMARY KEY(valor,utilizador_username,leilao_numero)
);

CREATE TABLE mensagem (
	texto		 VARCHAR(512),
	momento		 TIMESTAMP,
	publi		 BOOL NOT NULL,
	utilizador_username VARCHAR(512),
	leilao_numero	 INTEGER,
	PRIMARY KEY(momento,utilizador_username,leilao_numero)
);

CREATE TABLE utilizador (
	username VARCHAR(512),
	password VARCHAR(512) NOT NULL,
	PRIMARY KEY(username)
);

CREATE TABLE descricao (
	descricao	 VARCHAR(512) NOT NULL,
	leilao_numero INTEGER,
	PRIMARY KEY(descricao,leilao_numero)
);

CREATE TABLE titulo (
	titulo	 VARCHAR(512) NOT NULL,
	
	leilao_numero INTEGER,
	PRIMARY KEY(titulo,leilao_numero)
);

ALTER TABLE leilao ADD CONSTRAINT leilao_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE leilao ADD CONSTRAINT constraint_0 CHECK (preco_minimo > 0);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk2 FOREIGN KEY (leilao_numero) REFERENCES leilao(numero);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE mensagem ADD CONSTRAINT mensagem_fk2 FOREIGN KEY (leilao_numero) REFERENCES leilao(numero);
ALTER TABLE utilizador ADD CONSTRAINT constraint_0 CHECK (length(password) >5);
ALTER TABLE descricao ADD CONSTRAINT descricao_fk1 FOREIGN KEY (leilao_numero) REFERENCES leilao(numero);
ALTER TABLE titulo ADD CONSTRAINT titulo_fk1 FOREIGN KEY (leilao_numero) REFERENCES leilao(numero);


INSERT INTO UTILIZADOR VALUES ('Pearle Toomey','password');
INSERT INTO UTILIZADOR VALUES ('Bee Earley','password');
INSERT INTO UTILIZADOR VALUES ('Mitchel Scala','password');
INSERT INTO UTILIZADOR VALUES ('Bertram Pitts','password');
INSERT INTO UTILIZADOR VALUES ('Nadine Rosebrock','password');
INSERT INTO UTILIZADOR VALUES ('Christinia Christenson','password');
INSERT INTO UTILIZADOR VALUES ('Keesha Streich','password');
INSERT INTO UTILIZADOR VALUES ('Josiah Aronson','password');
INSERT INTO UTILIZADOR VALUES ('Stephine Bentley','password');
INSERT INTO UTILIZADOR VALUES ('Madison Eurich','password');
INSERT INTO UTILIZADOR VALUES ('Thelma Kiddy','password');
INSERT INTO UTILIZADOR VALUES ('Sheryl Wiersma','password');
INSERT INTO UTILIZADOR VALUES ('Rufus Surface','password');
INSERT INTO UTILIZADOR VALUES ('Remedios Beller','password');
INSERT INTO UTILIZADOR VALUES ('Hellen Hayward','password');
INSERT INTO UTILIZADOR VALUES ('Esperanza Hamed','password');
INSERT INTO UTILIZADOR VALUES ('Burma Thiele','password');
INSERT INTO UTILIZADOR VALUES ('Jimmie Ortega','password');
INSERT INTO UTILIZADOR VALUES ('Bertha Feldt','password');
INSERT INTO UTILIZADOR VALUES ('Freida Scarberry','password');
INSERT INTO UTILIZADOR VALUES ('Fransisca Tosi','password');
INSERT INTO UTILIZADOR VALUES ('Sid Brigance','password');
INSERT INTO UTILIZADOR VALUES ('Ivey Resch','password');
INSERT INTO UTILIZADOR VALUES ('Jacquiline Lou','password');
INSERT INTO UTILIZADOR VALUES ('Darlene Duvall','password');
INSERT INTO UTILIZADOR VALUES ('Marya Bush','password');
INSERT INTO UTILIZADOR VALUES ('Rosalie Rhoades','password');
INSERT INTO UTILIZADOR VALUES ('Mikki Luedtke','password');
INSERT INTO UTILIZADOR VALUES ('Shonna Mcdonnell','password');
INSERT INTO UTILIZADOR VALUES ('Idella Beckert','password');

insert into leilao (ean_artigo,preco_minimo,momento_fim,titulo,descricao,utilizador_username) values (2298,200,'2021-06-30','chair','19th century chair','Thelma Kiddy');
insert into leilao (ean_artigo,preco_minimo,momento_fim,titulo,descricao,utilizador_username) values (2358,750,'2021-06-13 22:00:00','tv','55 inch oled','Rufus Surface');
insert into leilao (ean_artigo,preco_minimo,momento_fim,titulo,descricao,utilizador_username) values (2138,25050,'2021-06-17','car','mercedes class a','Jacquiline Lou');
insert into leilao (ean_artigo,preco_minimo,momento_fim,titulo,descricao,utilizador_username) values (5794,150000,'2021-06-18 19:40:00','painting','Van Gogh original','Rufus Surface');
insert into leilao (ean_artigo,preco_minimo,momento_fim,titulo,descricao,utilizador_username) values (4578,375,'2021-06-10','Computer','ASUS Pc','Keesha Streich');
insert into leilao (ean_artigo,preco_minimo,momento_fim,titulo,descricao,utilizador_username) values (9145,457,'2021-07-01 23:00:00','Camera','Canon 550d','Pearle Toomey');


CREATE OR REPLACE PROCEDURE public.licitaUltrapassada(preco numeric,id_leilao numeric)
LANGUAGE 'plpgsql'
AS $BODY$
	declare
		utilizador licitacao.utilizador_username%type;
		msg mensagem.texto%type;
	begin
		SELECT utilizador_username from licitacao where leilao_numero = id_leilao  and valor = preco INTO utilizador;
		IF utilizador IS NOT NULL THEN
			msg:= FORMAT('A sua licitacao de %s euros no leilao %s foi ultrapassada!',preco,id_leilao);
			INSERT INTO mensagem (texto, momento,publi, utilizador_username,leilao_numero) VALUES (msg,CURRENT_TIMESTAMP,FALSE,utilizador,id_leilao);
		END IF;

end;
$BODY$;

CREATE OR REPLACE PROCEDURE public.licita(utilizador varchar, bid numeric,  id_leilao numeric)
LANGUAGE 'plpgsql'
AS $BODY$
	declare
		val licitacao.valor%type;
		minimo leilao.preco_minimo%type;
	begin
		lock table licitacao in exclusive mode;
		lock table leilao in exclusive mode;
		SELECT max(valor) from licitacao where leilao_numero = id_leilao INTO val;
		SELECT preco_minimo from leilao where numero = id_leilao INTO minimo;
		IF bid >= minimo THEN
			IF val IS NULL or bid > val THEN
				INSERT INTO licitacao (valor, momento, utilizador_username,leilao_numero) VALUES (bid, CURRENT_TIMESTAMP,utilizador, id_leilao);
				UPDATE leilao
				SET preco_vencedor = bid
				WHERE numero = id_leilao and ativo = TRUE;
				IF val IS NOT NULL THEN
					CALL licitaultrapassada(val,id_leilao);
				END IF;
			END IF;
		ELSE
			UPDATE leilao
			SET preco_vencedor =  val
			WHERE numero = id_leilao AND ativo = true;
		END IF;
end;
$BODY$;

create or replace function public.licitar(utilizador varchar, bid numeric,  id_leilao numeric)
returns varchar
LANGUAGE 'plpgsql'
AS $BODY$
declare
		val licitacao.valor%type;
		minimo leilao.preco_minimo%type;
		ative leilao.ativo%type;
		phrase leilao.titulo%type;
begin
	lock table licitacao in exclusive mode;
	lock table leilao in exclusive mode;
	SELECT ativo from leilao where numero = id_leilao INTO ative;
	IF ative is True THEN
		SELECT max(valor) from licitacao where leilao_numero = id_leilao INTO val;
		SELECT preco_minimo from leilao where numero = id_leilao INTO minimo;
		IF bid >= minimo THEN
			phrase:='bid maior que minimo';
			IF val IS NULL or bid > val THEN
				phrase:= FORMAT('A sua licitacao de %s euros no leilao %s foi superou a ultima licitacao de %s euros! O preco minimo e %s!',bid,id_leilao,val,minimo);
				INSERT INTO licitacao (valor, momento, utilizador_username,leilao_numero) VALUES (bid, CURRENT_TIMESTAMP,utilizador, id_leilao);
				UPDATE leilao
				SET preco_vencedor = bid
				WHERE numero = id_leilao and ativo = TRUE;
				IF val IS NOT NULL THEN
					CALL licitaultrapassada(val,id_leilao);
				END IF;
			ELSE
					phrase:= 'Licitacao abaixo da licitacao vencedora!';
			END IF;
		ELSE
			phrase:= 'Licitacao abaixo do valor minimo!';
		END IF;

	ELSE
		phrase:= 'Nenhum leilao ativo com esse numero encontrado';
	END IF;
	return phrase;
end


$BODY$;

CREATE OR REPLACE PROCEDURE public.newDescricao(descr VARCHAR,id_leilao numeric)
LANGUAGE 'plpgsql'
AS $BODY$
	declare
		old_descricao leilao.descricao%type;
		old_id leilao.numero%type;
	
	
	begin
		lock table leilao in exclusive mode;
		lock table titulo in exclusive mode;
		SELECT descricao FROM leilao where numero = id_leilao INTO  old_descricao;
		INSERT INTO descricao(descricao,leilao_numero) VALUES (old_descricao,id_leilao);
		
		UPDATE leilao
		SET descricao = descr
		WHERE leilao.numero = id_leilao;
	end;
	
	$BODY$;



CREATE OR REPLACE PROCEDURE public.newTitulo(tit VARCHAR,id_leilao numeric)
LANGUAGE 'plpgsql'
AS $BODY$
	declare
		old_titulo leilao.titulo%type;
		old_id leilao.numero%type;
	
	
	begin
		lock table leilao in exclusive mode;
		lock table titulo in exclusive mode;
		SELECT titulo FROM leilao where numero = id_leilao INTO  old_titulo;
		INSERT INTO titulo(titulo,leilao_numero) VALUES (old_titulo,id_leilao);
		
		UPDATE leilao
		SET titulo = tit
		WHERE leilao.numero = id_leilao;
	end;
	
	$BODY$;