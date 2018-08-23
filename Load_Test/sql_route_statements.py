SQL_ROUTES_STATEMENTS = {

    "User Recordings Ribbon": """
                                SELECT
                                u.{arg1}
                                FROM content_recordinguser u JOIN rsstuff_rsrecording r ON u.guid = r.user_guid
                                WHERE r.health_percent > 50 AND r.active AND r.state = 2 OR r.state = 3
                                GROUP BY u.guid
                                HAVING count (r.id) >= {min} AND count (r.id) <= {max}
    """,

    "User Franchise Ribbon": """
                                SELECT 
                                u.{arg1},
                                f.{arg2}
                                FROM content_recordinguser u JOIN rsstuff_rsrecording r ON u.guid = r.user_guid
	                            JOIN content_franchiserecordingrule f ON f.guid = r.rule
                                WHERE r.health_percent >  50 AND r.rec_start < now()
                                GROUP BY u.{arg1},
                                f.{arg2}
                                having count (r.id) >= {min} and count (r.id) <= {max}
    """,
    "User Recspace Information": """
    
                                SELECT 
                                u.{arg1}
                                FROM content_recordinguser u
    """,

        # There are 400 Test Users
    "Update User Settings": """
                                SELECT 
                                u.{arg1}
                                FROM content_recordinguser u
                                WHERE u.description = 'update_user_settings'
    
    """,

    "Create Recordings": """
                              SELECT
                              u.{arg1},
                              c.{arg2},
                              a.{arg3}
                              FROM content_recordinguser u, content_channel c, content_asset a
                              where a.channel_id = c.id and u.inactive = false and a.start > now()
                            
    """,
    "Protect Recordings": """
                              SELECT 
                              r.{arg1}
                              FROM content_recordinguser u JOIN rsstuff_rsrecording r
                              ON u.guid = r.user_guid
                              WHERE u.description = 'update_user_settings'
    
    """,
    "Mark Watched": """
                              SELECT u.guid
                              FROM rsstuff_rsrecording u
                              WHERE u.watched = TRUE 

    
    """,
    "Delete Recordings": """
                              SELECT
                              r.{arg1}
                              From rsstuff_rsrecording r
                              Where r.rec_start < now()
    """,
    "Create Rules": """
                              SELECT u.{arg1}
                              FROM content_recordinguser u 
                              LEFT JOIN content_franchiserecordingrule fr
	                          ON u.id = fr.user_id
                              GROUP BY u.{arg1}
                              HAVING count (fr.id) = 0
    
    """,
    "Update Rules": """
                              SELECT fr.{arg1}
                              FROM content_franchiserecordingrule fr JOIN content_recordinguser u
                              ON u.id = fr.user_id 
                              WHERE u.description = 'update_user_rules'
    
    """,
    "Delete Rules": """
                              SELECT fr.{arg1}
                              FROM content_franchiserecordingrule fr
    
    """,

    "List Rules": """
                              SELECT u.{arg1} FROM content_recordinguser u WHERE u.id IN 
                                (SELECT fr.user_id
                                FROM content_franchiserecordingrule fr
                                GROUP BY fr.user_id
                                HAVING count(fr.*) >= {min} AND count(fr.*) <= {max})
    
    """,

    "Redundant Ts Segment": """
                                
                                SELECT r.playback_qvt from rsstuff_rsrecording r
                                WHERE r.playable = TRUE and 
                                r.active = TRUE and 
                                r.rec_end < now() and 
                                r.health_percent = 100 and 
                                r.state = 3
                                LIMIT 1
    """,

}









TEST_SQL_STATEMENTS = {

        "Update User Settings": """
                                    SELECT 
                                    u.guid,
                                    u.rs_recspace
                                    FROM content_recordinguser u
                                    WHERE u.description = 'update_user_settings'
                                    
        """,

        "Protect Recordings": """
                                    SELECT 
                                    u.guid,
                                    r.protected
                                    FROM content_recordinguser u JOIN rsstuff_rsrecording r
                                    ON u.guid = r.user_guid
                                    WHERE u.description = 'update_user_settings'
        """,


        "Update Rules": """
                                 
                              SELECT
                              fr.mode
                              FROM content_recordinguser u JOIN content_franchiserecordingrule fr
                              ON u.id = fr.user_id
                              WHERE u.description = 'update_user_rules' AND u.id IN
                                (SELECT fr.user_id
                                FROM content_franchiserecordingrule fr
                                GROUP BY fr.user_id
                                HAVING count(fr.*) > 0)
        """
}



DATA_FACTORY_ROUTES = {

    "users_exist": """
                        SELECT
                        u.guid,
                        u.id
                        FROM content_recordinguser u 
                        WHERE u.description = '{desc}'
    """,

    "recs_exist": """
                                SELECT
                                u.guid,
                                count(r.id)
                                FROM content_recordinguser u JOIN {table_name} r ON u.guid = r.user_guid
                                WHERE {future} r.health_percent > 50 AND u.description = '{desc}'
                                GROUP BY 
                                u.guid
                                
    """,

    "franchise_recs_exist": """
                                SELECT 
                                u.guid,
                                count(r.id)
                                FROM content_recordinguser u JOIN {table_name} r ON u.guid = r.user_guid
	                            JOIN content_franchiserecordingrule f ON f.guid = r.rule
                                WHERE r.health_percent >  50 AND r.rec_start < now() AND u.description = '{desc}' AND f.franchise_guid = {franchise_guid}
                                GROUP BY
                                u.guid
    """,

    "rules_exist": """
                              SELECT 
                              u.guid,
                              count(fr.guid)
                              FROM content_franchiserecordingrule fr RIGHT JOIN content_recordinguser u
                              ON u.id = fr.user_id 
                              WHERE u.description = '{desc}' 
                              GROUP BY 
                              u.guid
    """,

    "user_guid_taken": """
            SELECT 
            u.id
            FROM content_recordinguser u
            WHERE u.guid = '{guid}'
    """,

    "user_guid_from_desc": """
            SELECT
            u.guid
            FROM content_recordinguser u
            WHERE u.description = '{desc}'
    
    """,

    "user_id_from_desc": """
                          SELECT
                          u.id
                          FROM content_recordinguser u
                          WHERE u.description = '{desc}'

    """,

    "delete_users": """
            DELETE FROM content_recordinguser u
            WHERE u.guid = '{guid}'
    
    """,

    "get_franchise_ids": """
            SELECT 
            f.guid
            FROM content_franchise f
            WHERE f.guid IS NOT NULL
            limit {count}
    """,

    "get_rec_ids": """
            SELECT
            a.external_id,
            c.guid
            FROM content_asset a JOIN content_channel c 
            ON a.channel_id = c.id
            FULL OUTER JOIN rsstuff_rsrecording r ON r.asset_id = a.id
            WHERE c.record = TRUE AND c.stream_cached = TRUE AND a.end > now()
            limit {count}
    """


}