<?php


class NFT{
    private $nft_data=[];

    public function __construct()
    {
        $this->nft_data['id'] = guidv4();
        return;
    }

    public function setNFTData($data){
        $data['price'] = intval($data['price']);
        $data['title'] = htmlspecialchars($data['title']);
        $data['data'] = htmlspecialchars($data['data']);
        $this->nft_data= array_merge($this->nft_data, $data);
    }


    public function setOwner($owner){
        $this->nft_data['owner'] = $owner;
    }


    public function getUrl() {
        return "http://" . $_SERVER['SERVER_NAME'] . ":3003" . "/view/" . $this->id;
    }

    public function mint(){
        $MINT_PATH = 'http://' . getenv('TRANSACTION_HOST') . '/mint';
        extract($this->nft_data);
        
        $post_data = [
            'price' => $price,
            'owner' => $owner,
            'data' => $data,
            'title' => $title,
            'public' => $public,
            'id' => $id
        ];
        $res = request_post($MINT_PATH, $post_data);
        if ($res == false) return false;
        $this->id = $res->new_id;
        return $res->success;

    }

}
